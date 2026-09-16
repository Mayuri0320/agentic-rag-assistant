"""Factory for creating language model providers."""

from app.agent.llm.base import LLMProvider
from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.openai import OpenAILLMProvider


class LLMProviderFactory:
    """Create the configured language model provider."""

    @staticmethod
    def create(
        *,
        provider: str,
        api_key: str,
        model: str,
    ) -> LLMProvider:
        """Create an LLM provider from configuration."""
        normalized_provider = provider.strip().lower()

        if normalized_provider == "mock":
            return MockLLMProvider()

        if normalized_provider == "openai":
            return OpenAILLMProvider(
                api_key=api_key,
                model=model,
            )

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )