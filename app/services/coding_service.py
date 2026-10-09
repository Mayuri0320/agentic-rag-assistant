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

The supplied source file is written in {source_language}.

The requested target language is {target_language}.

Your job is to understand the COMPLETE supplied source code and
perform the user's requested operation.

IMPORTANT TARGET-LANGUAGE RULES:

1. The final CODE section MUST contain actual {target_language}
   source code.
2. If the user requested a conversion, completely translate the
   implementation into {target_language}.
3. Do NOT simply rename the file extension.
4. Do NOT return the original {source_language} code when conversion
   was requested.
5. Do NOT mix source-language syntax with target-language syntax.
6. Preserve the original program's functionality and important logic.
7. Preserve classes, methods, algorithms, calculations, and behaviour
   wherever the target language supports equivalent functionality.
8. Replace language-specific libraries and constructs with appropriate
   {target_language} equivalents.
9. Return the COMPLETE resulting source file.
10. Do not use TODO placeholders.
11. Do not omit important functions, classes, imports, or logic.
12. Make the result internally consistent with {target_language}.

Return your response in EXACTLY this format:

---CODE---
<complete {target_language} source code>
---END CODE---

---EXPLANATION---
<clear explanation of the implementation>
---END EXPLANATION---

The explanation should:
- explain what the original code does;
- explain what was changed or converted;
- explain important classes, functions, and algorithms;
- mention important language-specific changes;
- mention assumptions or limitations;
- never claim that code was executed or tested unless it actually was.

Do not add text before ---CODE---.
Do not add text after ---END EXPLANATION---.
"""

        user_prompt = f"""
SOURCE LANGUAGE:
{source_language}

TARGET LANGUAGE:
{target_language}

USER INSTRUCTION:
{user_instruction}

SOURCE FILE:
{source_filename}

START OF SOURCE CODE
--------------------
{source_code}
--------------------
END OF SOURCE CODE

Now perform the requested operation.

The requested target language is {target_language}.
The CODE section MUST contain actual {target_language} code.
"""

        response = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        generated_code, explanation = self._parse_response(response)

        if not generated_code.strip():
            raise ValueError(
                "Gemini did not return generated source code.",
            )

        if not explanation.strip():
            raise ValueError(
                "Gemini did not return a solution explanation.",
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

        extension = Path(filename).suffix.lower()

        return cls.EXTENSION_LANGUAGES.get(extension)

    @classmethod
    def detect_target_language(
        cls,
        instruction: str,
        source_language: str,
    ) -> str:
        """Detect the requested target language from the instruction."""

        text = instruction.lower().strip()

        patterns = [
            r"\bto\s+(c\+\+|c#|java|python|javascript|typescript|"
            r"csharp|cpp|c|go|rust|php|ruby|swift|kotlin|scala|sql|"
            r"bash|shell)\b",
            r"\binto\s+(c\+\+|c#|java|python|javascript|typescript|"
            r"csharp|cpp|c|go|rust|php|ruby|swift|kotlin|scala|sql|"
            r"bash|shell)\b",
            r"\bconvert\s+(?:this|it|the\s+code)\s+(?:to|into)\s+"
            r"(c\+\+|c#|java|python|javascript|typescript|csharp|"
            r"cpp|c|go|rust|php|ruby|swift|kotlin|scala|sql|bash|shell)\b",
            r"\bwrite\s+(?:this|it|the\s+code)\s+in\s+"
            r"(c\+\+|c#|java|python|javascript|typescript|csharp|"
            r"cpp|c|go|rust|php|ruby|swift|kotlin|scala|sql|bash|shell)\b",
            r"\brewrite\s+(?:this|it|the\s+code)\s+(?:in|using)\s+"
            r"(c\+\+|c#|java|python|javascript|typescript|csharp|"
            r"cpp|c|go|rust|php|ruby|swift|kotlin|scala|sql|bash|shell)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                language = match.group(1).lower()

                if language == "cpp":
                    return "cpp"

                if language == "c#":
                    return "csharp"

                if language == "shell":
                    return "bash"

                if language == "c++":
                    return "cpp"

                return language

        return source_language

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str]:
        """Extract generated code and explanation."""

        if not isinstance(response, str) or not response.strip():
            raise ValueError("Gemini returned an empty response.")

        response = response.strip()

        code_start_marker = "---CODE---"
        code_end_marker = "---END CODE---"
        explanation_start_marker = "---EXPLANATION---"
        explanation_end_marker = "---END EXPLANATION---"

        code_start = response.find(code_start_marker)
        code_end = response.find(code_end_marker)

        explanation_start = response.find(explanation_start_marker)
        explanation_end = response.find(explanation_end_marker)

        if code_start == -1 or code_end == -1:
            raise ValueError(
                "Gemini response did not contain the required CODE section.",
            )

        if explanation_start == -1 or explanation_end == -1:
            raise ValueError(
                "Gemini response did not contain the required " "EXPLANATION section.",
            )

        if code_end <= code_start:
            raise ValueError("Gemini returned an invalid CODE section.")

        if explanation_end <= explanation_start:
            raise ValueError(
                "Gemini returned an invalid EXPLANATION section.",
            )

        generated_code = response[
            code_start + len(code_start_marker) : code_end
        ].strip()

        explanation = response[
            explanation_start + len(explanation_start_marker) : explanation_end
        ].strip()

        generated_code = CodingService._remove_code_fences(
            generated_code,
        )

        return generated_code, explanation

    @staticmethod
    def _remove_code_fences(code: str) -> str:
        """Remove optional Markdown code fences."""

        code = code.strip()

        if code.startswith("```"):
            lines = code.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            code = "\n".join(lines)

        return code.strip()
