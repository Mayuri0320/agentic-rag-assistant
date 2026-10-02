"""Web search service."""

from __future__ import annotations

import html
import re

import httpx


class WebSearchService:
    """Search the public web and return structured results."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, timeout: float = 10.0) -> None:
        """Initialize the web search service."""
        self._timeout = timeout

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[dict[str, str]]:
        """Search the web and return title, URL, and snippet."""
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if max_results <= 0:
            raise ValueError("max_results must be greater than zero.")

        response = httpx.post(
            self.SEARCH_URL,
            data={"q": query},
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
                )
            },
            timeout=self._timeout,
            follow_redirects=True,
        )

        response.raise_for_status()

        return self._parse_results(
            response.text,
            max_results=max_results,
        )

    @staticmethod
    def _parse_results(
        html_content: str,
        *,
        max_results: int,
    ) -> list[dict[str, str]]:
        """Extract organic search results from DuckDuckGo HTML."""
        result_pattern = re.compile(
            r'<div[^>]+class="result[^"]*"[^>]*>(.*?)</div>\s*</div>',
            re.IGNORECASE | re.DOTALL,
        )

        title_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>' r"(.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )

        snippet_pattern = re.compile(
            r'<a[^>]+class="result__snippet"[^>]*>'
            r"(.*?)</a>|"
            r'<div[^>]+class="result__snippet"[^>]*>'
            r"(.*?)</div>",
            re.IGNORECASE | re.DOTALL,
        )

        results: list[dict[str, str]] = []

        for result_block in result_pattern.findall(html_content):
            title_match = title_pattern.search(result_block)

            if title_match is None:
                continue

            url = html.unescape(title_match.group(1))
            title = WebSearchService._clean_html(title_match.group(2))

            # Ignore DuckDuckGo advertisements and tracking URLs.
            if "y.js?" in url or "ad_domain=" in url:
                continue

            if not title or not url.startswith(("http://", "https://")):
                continue

            snippet_match = snippet_pattern.search(result_block)
            snippet = ""

            if snippet_match:
                snippet = WebSearchService._clean_html(
                    snippet_match.group(1) or snippet_match.group(2) or ""
                )

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

            if len(results) >= max_results:
                break

        return results

    @staticmethod
    def _clean_html(value: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        value = re.sub(r"<[^>]+>", "", value)
        value = html.unescape(value)
        return " ".join(value.split())
