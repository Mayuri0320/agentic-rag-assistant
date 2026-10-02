"""Tests for the web search service."""

import httpx
import pytest

from app.services.web_search_service import WebSearchService


def test_search_rejects_blank_query() -> None:
    """Blank search queries should be rejected."""
    service = WebSearchService()

    with pytest.raises(ValueError, match="Search query cannot be empty"):
        service.search("   ")


def test_search_rejects_invalid_max_results() -> None:
    """The result limit must be greater than zero."""
    service = WebSearchService()

    with pytest.raises(
        ValueError,
        match="max_results must be greater than zero",
    ):
        service.search("artificial intelligence", max_results=0)


def test_parse_results_returns_organic_results() -> None:
    """Organic DuckDuckGo results should be parsed correctly."""
    html_content = """
    <div class="result">
        <div>
            <a class="result__a"
               href="https://example.com/article">
                Example Article
            </a>
        </div>
    </div>
    """

    results = WebSearchService._parse_results(
        html_content,
        max_results=5,
    )

    assert results == [
        {
            "title": "Example Article",
            "url": "https://example.com/article",
            "snippet": "",
        }
    ]


def test_parse_results_filters_tracking_urls() -> None:
    """Tracking and advertisement URLs should be ignored."""
    html_content = """
    <div class="result">
        <div>
            <a class="result__a"
               href="https://example.com/y.js?ad_domain=test">
                Advertisement
            </a>
        </div>
    </div>

    <div class="result">
        <div>
            <a class="result__a"
               href="https://example.com/real-article">
                Real Article
            </a>
        </div>
    </div>
    """

    results = WebSearchService._parse_results(
        html_content,
        max_results=5,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Real Article"
    assert results[0]["url"] == "https://example.com/real-article"


def test_parse_results_respects_max_results() -> None:
    """Search results should be limited to the requested number."""
    html_content = """
    <div class="result">
        <div>
            <a class="result__a"
               href="https://example.com/one">
                Result One
            </a>
        </div>
    </div>

    <div class="result">
        <div>
            <a class="result__a"
               href="https://example.com/two">
                Result Two
            </a>
        </div>
    </div>
    """

    results = WebSearchService._parse_results(
        html_content,
        max_results=1,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Result One"


def test_search_raises_for_http_error(monkeypatch) -> None:
    """HTTP errors should be propagated to the caller."""

    def mock_post(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "https://html.duckduckgo.com/html/",
        )
        response = httpx.Response(
            status_code=500,
            request=request,
        )
        return response

    monkeypatch.setattr(httpx, "post", mock_post)

    service = WebSearchService()

    with pytest.raises(httpx.HTTPStatusError):
        service.search("artificial intelligence")