"""Tests for the LLM provider factory."""

import pytest

from app.agent.llm.factory import LLMProviderFactory
from app.agent.llm.gemini import GeminiLLMProvider
from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.openai import OpenAILLMProvider


def test_factory_creates_mock_provider() -> None:
    """The factory should create a mock provider."""
    provider = LLMProviderFactory.create(
        provider="mock",
        api_key="",
        model="gpt-4.1-mini",
    )

    assert isinstance(provider, MockLLMProvider)


def test_factory_creates_openai_provider() -> None:
    """The factory should create an OpenAI provider."""
    provider = LLMProviderFactory.create(
        provider="openai",
        api_key="test-key",
        model="gpt-4.1-mini",
    )

    assert isinstance(provider, OpenAILLMProvider)


def test_factory_creates_gemini_provider() -> None:
    """The factory should create a Gemini provider."""
    provider = LLMProviderFactory.create(
        provider="gemini",
        api_key="test-key",
        model="gemini-2.5-flash",
    )

    assert isinstance(provider, GeminiLLMProvider)


def test_factory_is_case_insensitive() -> None:
    """Provider names should be case insensitive."""
    provider = LLMProviderFactory.create(
        provider="OPENAI",
        api_key="test-key",
        model="gpt-4.1-mini",
    )

    assert isinstance(provider, OpenAILLMProvider)


def test_factory_rejects_unknown_provider() -> None:
    """Unknown providers should be rejected."""
    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        LLMProviderFactory.create(
            provider="unknown",
            api_key="",
            model="gpt-4.1-mini",
        )
