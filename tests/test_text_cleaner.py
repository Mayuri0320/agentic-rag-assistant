"""Tests for text cleaning and normalization."""

from app.ingestion.cleaning.text_cleaner import TextCleaner


def test_clean_empty_text() -> None:
    """Empty input should return an empty string."""
    assert TextCleaner().clean("") == ""


def test_normalizes_newlines() -> None:
    """Different newline styles should be normalized."""
    text = "First\r\nSecond\rThird"

    result = TextCleaner().clean(text)

    assert result == "First\nSecond\nThird"


def test_removes_excessive_spaces() -> None:
    """Repeated spaces should be collapsed."""
    text = "Agentic     RAG\t\tAssistant"

    result = TextCleaner().clean(text)

    assert result == "Agentic RAG Assistant"


def test_preserves_paragraphs() -> None:
    """Paragraph separation should be preserved."""
    text = "First paragraph.\n\n\n\nSecond paragraph."

    result = TextCleaner().clean(text)

    assert result == "First paragraph.\n\nSecond paragraph."


def test_removes_spaces_before_punctuation() -> None:
    """Whitespace before punctuation should be removed."""
    text = "Hello world ! This is a test ."

    result = TextCleaner().clean(text)

    assert result == "Hello world! This is a test."


def test_repairs_broken_hyphenation() -> None:
    """Line-break hyphenation should be repaired."""
    text = "This is a docu-\nment."

    result = TextCleaner().clean(text)

    assert result == "This is a document."


def test_normalizes_unicode() -> None:
    """Unicode compatibility characters should be normalized."""
    text = "Ａｇｅｎｔｉｃ ＲＡＧ"

    result = TextCleaner().clean(text)

    assert result == "Agentic RAG"


def test_removes_control_characters() -> None:
    """Unwanted control characters should be removed."""
    text = "Hello\x00world\x01test"

    result = TextCleaner().clean(text)

    assert result == "Helloworldtest"


def test_strips_lines_and_document() -> None:
    """Leading and trailing whitespace should be removed."""
    text = "   First line   \n   Second line   "

    result = TextCleaner().clean(text)

    assert result == "First line\nSecond line"
