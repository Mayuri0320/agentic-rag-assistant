
"""Google Gemini language model provider."""

import time

from google import genai
from google.genai.errors import ServerError

from app.agent.llm.base import LLMProvider


class GeminiLLMProvider(LLMProvider):
    """Generate responses using the Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
    ) -> None:
        """Initialize the Gemini provider."""
        if not api_key.strip():
            raise ValueError("Gemini API key cannot be empty.")

        if not model.strip():
            raise ValueError("Gemini model cannot be empty.")

        self._client = genai.Client(
            api_key=api_key,
            http_options={
                "retry_options": {
                    "attempts": 1,
                },
            },
        )
        self._model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response using Gemini with retries for temporary failures."""
        if not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty.")

        if not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        for attempt in range(3):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config={"system_instruction": system_prompt},
                )

                if response.text is None:
                    raise ValueError("Gemini returned an empty response.")

                return response.text

            except ServerError:
                if attempt == 2:
                    raise
                time.sleep(2 ** (attempt + 1))

        raise RuntimeError("Gemini request failed after retries.")