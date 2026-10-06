"""Service for generating and validating Python assignment solutions."""

import ast
import json
from typing import Any

from app.agent.llm.base import LLMProvider


class CodingService:
    """Generate Python solutions and explain their implementation."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the coding service."""
        self.llm_provider = llm_provider

    def generate_solution(
        self,
        *,
        source_code: str,
        user_instruction: str,
    ) -> dict[str, str]:
        """Generate a complete Python solution and its explanation."""

        if not source_code.strip():
            raise ValueError("Source code cannot be empty.")

        if not user_instruction.strip():
            raise ValueError("User instruction cannot be empty.")

        system_prompt = """
You are an expert Python coding assistant and programming tutor.

Complete the user's Python assignment and explain your implementation.

Return exactly one valid JSON object with these two string fields:
{
  "solution_code": "complete Python source code",
  "explanation": "detailed explanation of the solution"
}

Requirements for solution_code:
1. Read the entire supplied Python source code.
2. Follow the user's requirements carefully.
3. Preserve existing structure and functionality where possible.
4. Implement the requested functionality completely.
5. Include all required functions and classes.
6. Avoid placeholders such as TODO or "implement here".
7. Generate valid Python syntax.

Requirements for explanation:
1. Explain your understanding of the assignment.
2. Describe the important changes made to the starter code.
3. Explain the algorithm and important functions.
4. Walk through how the solution works step by step.
5. Include relevant edge cases and assumptions.
6. Provide example inputs and outputs when useful.
7. Explain time and space complexity when meaningful.
8. Never claim tests were executed unless they actually were.

IMPORTANT JSON RULES:
- Return JSON only, without Markdown fences.
- Both values must be JSON strings.
- Escape newlines, quotation marks, and backslashes correctly
  inside JSON string values.
- Do not add any text before or after the JSON object.
"""

        user_prompt = f"""
USER INSTRUCTION:
{user_instruction}

STARTER PYTHON CODE:
--------------------
{source_code}
--------------------

Generate the complete Python solution and explain it.
"""

        response = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        result = self._parse_response(response)

        generated_code = result.get("solution_code")
        explanation = result.get("explanation")

        if not isinstance(generated_code, str) or not generated_code.strip():
            raise ValueError("Gemini did not return valid Python solution code.")

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("Gemini did not return a solution explanation.")

        self._validate_python(generated_code)

        return {
            "solution_code": generated_code.strip(),
            "explanation": explanation.strip(),
        }

    @classmethod
    def _parse_response(cls, response: str) -> dict[str, Any]:
        """Parse a JSON object from Gemini's response."""

        if not isinstance(response, str) or not response.strip():
            raise ValueError("Gemini returned an empty response.")

        cleaned_response = cls._clean_code(response)

        # Try parsing the complete response first.
        try:
            result = json.loads(cleaned_response)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Allow explanatory text before or after a valid JSON object.
        decoder = json.JSONDecoder()

        for index, character in enumerate(cleaned_response):
            if character != "{":
                continue

            try:
                result, _ = decoder.raw_decode(cleaned_response[index:])
            except json.JSONDecodeError:
                continue

            if isinstance(result, dict):
                return result

        raise ValueError(
            "Gemini returned an invalid response format. " "Please try again."
        )

    @staticmethod
    def _clean_code(response: str) -> str:
        """Remove Markdown fences around the response if present."""

        response = response.strip()

        if response.startswith("```"):
            lines = response.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            response = "\n".join(lines)

        return response.strip()

    @staticmethod
    def _validate_python(code: str) -> None:
        """Validate generated Python syntax."""

        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError(
                f"Generated Python contains a syntax error: {exc}"
            ) from exc
