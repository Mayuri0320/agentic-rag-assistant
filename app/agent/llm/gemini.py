"""Google Gemini language model provider."""

from google import genai

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

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response using the Gemini API."""
        if not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty.")

        if not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
            },
        )

        if response.text is None:
            raise ValueError("Gemini returned an empty response.")

        return response.text