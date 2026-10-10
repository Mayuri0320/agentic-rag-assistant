"""Service for generating and converting source code."""

import re
from pathlib import Path

from app.agent.llm.base import LLMProvider


class CodingService:
    """Generate, convert, fix, and explain source code."""

    LANGUAGE_EXTENSIONS = {
        "python": ".py",
        "java": ".java",
        "javascript": ".js",
        "typescript": ".ts",
        "cpp": ".cpp",
        "c++": ".cpp",
        "c": ".c",
        "csharp": ".cs",
        "c#": ".cs",
        "go": ".go",
        "rust": ".rs",
        "php": ".php",
        "ruby": ".rb",
        "swift": ".swift",
        "kotlin": ".kt",
        "scala": ".scala",
        "sql": ".sql",
        "bash": ".sh",
        "shell": ".sh",
    }

    EXTENSION_LANGUAGES = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".scala": "scala",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
    }

    LANGUAGE_ALIASES = {
        "python": "python",
        "py": "python",
        "java": "java",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "cpp": "cpp",
        "c++": "cpp",
        "c": "c",
        "csharp": "csharp",
        "c#": "csharp",
        "go": "go",
        "golang": "go",
        "rust": "rust",
        "php": "php",
        "ruby": "ruby",
        "swift": "swift",
        "kotlin": "kotlin",
        "scala": "scala",
        "sql": "sql",
        "bash": "bash",
        "shell": "bash",
    }

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the coding service."""
        self.llm_provider = llm_provider

    def generate_solution(
        self,
        *,
        source_code: str,
        user_instruction: str,
        source_filename: str = "solution.py",
    ) -> dict[str, str]:
        """Generate or convert source code according to the instruction."""
        if not source_code.strip():
            raise ValueError("Source code cannot be empty.")

        if not user_instruction.strip():
            raise ValueError("User instruction cannot be empty.")

        source_language = self.detect_language_from_filename(
            source_filename,
        )

        if source_language is None:
            raise ValueError(
                f"Unsupported source file type: {Path(source_filename).suffix}",
            )

        target_language = self.detect_target_language(
            user_instruction,
            source_language,
        )
        extension = self.LANGUAGE_EXTENSIONS[target_language]

        system_prompt = f"""
You are an expert software engineer and programming language
conversion specialist.

SOURCE LANGUAGE: {source_language}
REQUIRED OUTPUT LANGUAGE: {target_language}

Follow the user's instruction, but the required output language above
is authoritative for the generated source file.

Rules:
1. Return complete source code in {target_language}.
2. If source and target languages differ, translate the implementation;
   do not merely rename the file or preserve the original language.
3. Preserve important algorithms, classes, functions, and behaviour.
4. Use appropriate standard-library or equivalent target-language
   constructs where possible.
5. Do not silently omit important functionality. Explain genuine
   limitations honestly.
6. Never claim the code was executed or tested unless it actually was.
7. Do not put explanatory prose inside the source code.
8. The explanation must describe the actual source and target languages
   and the changes requested by the user.
9. If the requested target is the same as the source, improve or preserve
   that language rather than inventing a different conversion.

Return the response in this format:

---CODE---
Complete source file here
---END CODE---

---EXPLANATION---
Explain the changes here
---END EXPLANATION---

Do not put introductory text before the code section.
"""

        user_prompt = f"""
SOURCE LANGUAGE: {source_language}
REQUIRED OUTPUT LANGUAGE: {target_language}
OUTPUT FILE EXTENSION: {extension}

USER INSTRUCTION:
{user_instruction}

SOURCE FILE:
{source_filename}

SOURCE CODE:
--------------------
{source_code}
--------------------

Generate the complete result now.

The output language must be {target_language}, regardless of the
language used in the source file or in any previous conversation.
"""

        response = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        generated_code, explanation = self._parse_response(response)

        if not generated_code.strip():
            raise ValueError("The model did not return generated source code.")

        self._validate_target_language(
            generated_code,
            source_language,
            target_language,
        )

        if not explanation.strip():
            explanation = (
                f"Generated a {target_language} source file from "
                f"{source_language} input according to the requested "
                "instruction. Review and test the generated code before "
                "using it in production."
            )

        return {
            "solution_code": generated_code.strip(),
            "explanation": explanation.strip(),
            "language": target_language,
            "extension": extension,
        }

    @classmethod
    def detect_language_from_filename(
        cls,
        filename: str,
    ) -> str | None:
        """Detect the source language from a filename."""
        return cls.EXTENSION_LANGUAGES.get(
            Path(filename).suffix.lower(),
        )

    @classmethod
    def detect_target_language(
        cls,
        instruction: str,
        source_language: str,
    ) -> str:
        """Detect the explicitly requested output language."""
        text = instruction.lower().strip()

        aliases = sorted(
            cls.LANGUAGE_ALIASES,
            key=len,
            reverse=True,
        )
        language_pattern = "|".join(re.escape(alias) for alias in aliases)
        language_pattern = rf"(?<![a-z0-9_+#])({language_pattern})(?![a-z0-9_])"

        # Prefer a language specified in an explicit conversion phrase.
        action_pattern = re.compile(
            rf"\b(?:convert|translate|rewrite|port|transform|change|"
            rf"write|implement|generate)\b.{{0,120}}?"
            rf"\b(?:to|into|in|using|as)\s+{language_pattern}",
            re.IGNORECASE,
        )
        matches = list(action_pattern.finditer(text))

        if matches:
            alias = matches[-1].group(1).lower()
            return cls.LANGUAGE_ALIASES[alias]

        # Handle requests such as "write this in Java" or
        # "please give the code in Python".
        direction_pattern = re.compile(
            rf"\b(?:to|into|in|using|as)\s+{language_pattern}",
            re.IGNORECASE,
        )
        matches = list(direction_pattern.finditer(text))

        if matches:
            alias = matches[-1].group(1).lower()
            return cls.LANGUAGE_ALIASES[alias]

        # Infer the language from an explicitly requested output extension.
        extension_matches = list(
            re.finditer(
                r"\.(py|java|js|ts|cpp|c|cs|go|rs|php|rb|swift|" r"kt|scala|sql|sh)\b",
                text,
                re.IGNORECASE,
            )
        )

        if extension_matches:
            extension = f".{extension_matches[-1].group(1).lower()}"
            language = cls.EXTENSION_LANGUAGES.get(extension)

            if language is not None:
                return language

        # Same-language editing is the fallback when no target is specified.
        return source_language

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str]:
        """Extract code and explanation, tolerating optional markers."""
        if not isinstance(response, str) or not response.strip():
            raise ValueError("The model returned an empty response.")

        response = response.strip()

        code_start_pattern = re.compile(
            r"(?im)^\s*(?:---\s*CODE\s*---|<CODE>|CODE\s*:)\s*"
        )
        code_end_pattern = re.compile(r"(?im)^\s*(?:---\s*END\s+CODE\s*---|</CODE>)\s*")
        explanation_start_pattern = re.compile(
            r"(?im)^\s*(?:---\s*EXPLANATION\s*---|" r"<EXPLANATION>|EXPLANATION\s*:)\s*"
        )
        explanation_end_pattern = re.compile(
            r"(?im)^\s*(?:---\s*END\s+EXPLANATION\s*---|" r"</EXPLANATION>)\s*"
        )

        code_start = code_start_pattern.search(response)
        explanation_start = explanation_start_pattern.search(response)

        if code_start:
            content_start = code_start.end()
            possible_ends = [
                match.start()
                for pattern in (
                    code_end_pattern,
                    explanation_start_pattern,
                )
                if (match := pattern.search(response, content_start))
            ]
            content_end = min(possible_ends, default=len(response))
            generated_code = response[content_start:content_end].strip()
        else:
            # Some model responses contain a fenced code block without
            # the requested CODE marker.
            fenced_blocks = re.findall(
                r"```[^\n`]*\n(.*?)```",
                response,
                re.DOTALL,
            )
            if fenced_blocks:
                generated_code = fenced_blocks[0].strip()
            else:
                raise ValueError(
                    "The model response did not contain a recognisable "
                    "code section or fenced code block.",
                )

        explanation = ""

        if explanation_start:
            explanation_content_start = explanation_start.end()
            explanation_end = explanation_end_pattern.search(
                response,
                explanation_content_start,
            )
            content_end = explanation_end.start() if explanation_end else len(response)
            explanation = response[explanation_content_start:content_end].strip()

        generated_code = CodingService._remove_code_fences(
            generated_code,
        )

        return generated_code, explanation

    @staticmethod
    def _validate_target_language(
        code: str,
        source_language: str,
        target_language: str,
    ) -> None:
        """Reject clearly identifiable output in the wrong language."""
        if source_language == target_language:
            return

        wrong_language_patterns = {
            "python": [
                r"^\s*#include\s*[<\"]",
                r"\bpublic\s+class\s+\w+",
                r"\bSystem\.out\.",
                r"\bconsole\.log\s*\(",
                r"^\s*func\s+\w+\s*\(",
                r"^\s*fn\s+\w+\s*\(",
            ],
            "java": [
                r"^\s*def\s+\w+\s*\(",
                r"\bself\b",
                r"\bNone\b",
                r"\belif\b",
                r"if\s+__name__\s*==",
                r"^\s*#include\s*[<\"]",
            ],
            "javascript": [
                r"^\s*def\s+\w+\s*\(",
                r"if\s+__name__\s*==",
                r"\bSystem\.out\.",
            ],
            "typescript": [
                r"^\s*def\s+\w+\s*\(",
                r"if\s+__name__\s*==",
                r"\bSystem\.out\.",
            ],
            "cpp": [
                r"^\s*def\s+\w+\s*\(",
                r"\bSystem\.out\.",
                r"if\s+__name__\s*==",
            ],
        }

        patterns = wrong_language_patterns.get(target_language, [])
        matches = sum(
            bool(re.search(pattern, code, re.MULTILINE)) for pattern in patterns
        )

        # Require multiple indicators for Python/JavaScript/TypeScript,
        # where a single token can occur legitimately in other languages.
        threshold = (
            2
            if target_language
            in {
                "python",
                "javascript",
                "typescript",
            }
            else 1
        )

        if matches >= threshold:
            raise ValueError(
                f"The model returned code that appears inconsistent "
                f"with the requested {target_language} target language. "
                "Please retry the generation.",
            )

    @staticmethod
    def _remove_code_fences(code: str) -> str:
        """Remove optional Markdown code fences around the source."""
        code = code.strip()

        if code.startswith("```"):
            lines = code.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]

            code = "\n".join(lines)

        return code.strip()
