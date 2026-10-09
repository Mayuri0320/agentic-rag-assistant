"""Deterministic mock language model provider for testing."""

from app.agent.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Simple deterministic LLM implementation for tests."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_mime_type: str | None = None,
    ) -> str:
        """Generate a deterministic response."""
        del system_prompt
        del response_mime_type

        if not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty")

        return f"Mock answer based on the provided context:\n\n{user_prompt}"