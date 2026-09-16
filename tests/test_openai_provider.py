"""Tests for the OpenAI LLM provider."""

from unittest.mock import MagicMock, patch

import pytest

from app.agent.llm.openai import OpenAILLMProvider


def test_empty_api_key_is_rejected() -> None:
    """An empty API key must be rejected."""
    with pytest.raises(
        ValueError,
        match="OpenAI API key cannot be empty",
    ):
        OpenAILLMProvider(api_key="")


def test_whitespace_api_key_is_rejected() -> None:
    """A whitespace-only API key must be rejected."""
    with pytest.raises(
        ValueError,
        match="OpenAI API key cannot be empty",
    ):
        OpenAILLMProvider(api_key="   ")


def test_empty_model_is_rejected() -> None:
    """An empty model must be rejected."""
    with pytest.raises(
        ValueError,
        match="OpenAI model cannot be empty",
    ):
        OpenAILLMProvider(
            api_key="test-key",
            model="",
        )


def test_whitespace_model_is_rejected() -> None:
    """A whitespace-only model must be rejected."""
    with pytest.raises(
        ValueError,
        match="OpenAI model cannot be empty",
    ):
        OpenAILLMProvider(
            api_key="test-key",
            model="   ",
        )


def test_empty_system_prompt_is_rejected() -> None:
    """An empty system prompt must be rejected."""
    provider = OpenAILLMProvider(api_key="test-key")

    with pytest.raises(
        ValueError,
        match="system_prompt cannot be empty",
    ):
        provider.generate(
            system_prompt="",
            user_prompt="Hello",
        )


def test_empty_user_prompt_is_rejected() -> None:
    """An empty user prompt must be rejected."""
    provider = OpenAILLMProvider(api_key="test-key")

    with pytest.raises(
        ValueError,
        match="user_prompt cannot be empty",
    ):
        provider.generate(
            system_prompt="You are helpful.",
            user_prompt="",
        )


@patch("app.agent.llm.openai.OpenAI")
def test_generate_returns_openai_response(
    mock_openai: MagicMock,
) -> None:
    """The provider should return the generated OpenAI response."""
    mock_client = MagicMock()
    mock_response = MagicMock()

    mock_response.output_text = "This is the generated answer."
    mock_client.responses.create.return_value = mock_response
    mock_openai.return_value = mock_client

    provider = OpenAILLMProvider(
        api_key="test-key",
        model="gpt-4.1-mini",
    )

    result = provider.generate(
        system_prompt="You are a document assistant.",
        user_prompt="What is machine learning?",
    )

    assert result == "This is the generated answer."

    mock_openai.assert_called_once_with(
        api_key="test-key",
    )

    mock_client.responses.create.assert_called_once_with(
        model="gpt-4.1-mini",
        instructions="You are a document assistant.",
        input="What is machine learning?",
    )


@patch("app.agent.llm.openai.OpenAI")
def test_generate_propagates_openai_errors(
    mock_openai: MagicMock,
) -> None:
    """OpenAI API errors should be propagated to the caller."""
    mock_client = MagicMock()

    mock_client.responses.create.side_effect = RuntimeError(
        "OpenAI request failed"
    )

    mock_openai.return_value = mock_client

    provider = OpenAILLMProvider(api_key="test-key")

    with pytest.raises(
        RuntimeError,
        match="OpenAI request failed",
    ):
        provider.generate(
            system_prompt="You are helpful.",
            user_prompt="Hello",
        )