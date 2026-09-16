"""OpenAI language model provider."""

from openai import OpenAI

from app.agent.llm.base import LLMProvider


class OpenAILLMProvider(LLMProvider):
    """Generate responses using the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5.6-luna",
    ) -> None:
        """Initialize the OpenAI provider."""
        if not api_key.strip():
            raise ValueError("OpenAI API key cannot be empty.")

        if not model.strip():
            raise ValueError("OpenAI model cannot be empty.")

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response using the OpenAI Responses API."""
        if not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty.")

        if not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        response = self._client.responses.create(
            model=self._model,
            instructions=system_prompt,
            input=user_prompt,
        )

        return response.output_text