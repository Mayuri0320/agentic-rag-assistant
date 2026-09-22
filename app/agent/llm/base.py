"""Base abstractions for language model providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for language model providers."""

    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response from the language model."""
        raise NotImplementedError
