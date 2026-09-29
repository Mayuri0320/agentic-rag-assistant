"""Tests for the Gemini LLM provider."""

from unittest.mock import MagicMock, patch

import pytest

from app.agent.llm.gemini import GeminiLLMProvider


def test_empty_api_key_is_rejected() -> None:
    """An empty API key must be rejected."""
    with pytest.raises(
        ValueError,
        match="Gemini API key cannot be empty",
    ):
        GeminiLLMProvider(api_key="")


def test_whitespace_api_key_is_rejected() -> None:
    """A whitespace-only API key must be rejected."""
    with pytest.raises(
        ValueError,
        match="Gemini API key cannot be empty",
    ):
        GeminiLLMProvider(api_key="   ")


def test_empty_model_is_rejected() -> None:
    """An empty model must be rejected."""
    with pytest.raises(
        ValueError,
        match="Gemini model cannot be empty",
    ):
        GeminiLLMProvider(
            api_key="test-key",
            model="",
        )


def test_whitespace_model_is_rejected() -> None:
    """A whitespace-only model must be rejected."""
    with pytest.raises(
        ValueError,
        match="Gemini model cannot be empty",
    ):
        GeminiLLMProvider(
            api_key="test-key",
            model="   ",
        )


def test_empty_system_prompt_is_rejected() -> None:
    """An empty system prompt must be rejected."""
    provider = GeminiLLMProvider(api_key="test-key")

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
    provider = GeminiLLMProvider(api_key="test-key")

    with pytest.raises(
        ValueError,
        match="user_prompt cannot be empty",
    ):
        provider.generate(
            system_prompt="You are helpful.",
            user_prompt="",
        )


@patch("app.agent.llm.gemini.genai.Client")
def test_generate_returns_gemini_response(
    mock_client_class: MagicMock,
) -> None:
    """The provider should return the generated Gemini response."""
    mock_client = MagicMock()
    mock_response = MagicMock()

    mock_response.text = "This is the Gemini answer."
    mock_client.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client

    provider = GeminiLLMProvider(
        api_key="test-key",
        model="gemini-2.5-flash",
    )

    result = provider.generate(
        system_prompt="You are a document assistant.",
        user_prompt="What is machine learning?",
    )

    assert result == "This is the Gemini answer."

    mock_client_class.assert_called_once_with(
        api_key="test-key",
    )

    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-2.5-flash",
        contents="What is machine learning?",
        config={
            "system_instruction": "You are a document assistant.",
        },
    )


@patch("app.agent.llm.gemini.genai.Client")
def test_generate_rejects_empty_response(
    mock_client_class: MagicMock,
) -> None:
    """An empty Gemini response should be rejected."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = None

    mock_client.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client

    provider = GeminiLLMProvider(api_key="test-key")

    with pytest.raises(
        ValueError,
        match="Gemini returned an empty response",
    ):
        provider.generate(
            system_prompt="You are helpful.",
            user_prompt="Hello",
        )


@patch("app.agent.llm.gemini.genai.Client")
def test_generate_propagates_gemini_errors(
    mock_client_class: MagicMock,
) -> None:
    """Gemini API errors should be propagated to the caller."""
    mock_client = MagicMock()

    mock_client.models.generate_content.side_effect = RuntimeError(
        "Gemini request failed",
    )

    mock_client_class.return_value = mock_client

    provider = GeminiLLMProvider(api_key="test-key")

    with pytest.raises(
        RuntimeError,
        match="Gemini request failed",
    ):
        provider.generate(
            system_prompt="You are helpful.",
            user_prompt="Hello",
        )
