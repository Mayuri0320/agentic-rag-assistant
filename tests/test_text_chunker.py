"""Tests for document text chunking."""

import pytest

from app.ingestion.chunking.models import DocumentChunk
from app.ingestion.chunking.text_chunker import TextChunker


def test_empty_text_returns_no_chunks() -> None:
    """Empty text should produce no chunks."""
    chunker = TextChunker()

    assert chunker.split_text("") == []


def test_whitespace_only_text_returns_no_chunks() -> None:
    """Whitespace-only text should produce no chunks."""
    chunker = TextChunker()

    assert chunker.split_text("   \n\n   ") == []


def test_short_text_creates_single_chunk() -> None:
    """Text shorter than the chunk size should remain intact."""
    chunker = TextChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.split_text("Hello world.")

    assert len(chunks) == 1
    assert chunks[0].text == "Hello world."
    assert chunks[0].chunk_index == 0


def test_chunks_have_sequential_indexes() -> None:
    """Chunk indexes should start at zero and increase sequentially."""
    text = "word " * 100

    chunker = TextChunker(
        chunk_size=50,
        chunk_overlap=10,
    )

    chunks = chunker.split_text(text)

    assert len(chunks) > 1
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_chunk_text_does_not_exceed_configured_size() -> None:
    """Chunks should not exceed the configured size."""
    text = "word " * 100

    chunker = TextChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.split_text(text)

    assert all(len(chunk.text) <= 100 for chunk in chunks)


def test_chunks_preserve_document_order() -> None:
    """Chunks should preserve the order of the source text."""
    text = (
        "First paragraph contains important information.\n\n"
        "Second paragraph contains more information.\n\n"
        "Third paragraph contains final information."
    )

    chunker = TextChunker(
        chunk_size=70,
        chunk_overlap=10,
    )

    chunks = chunker.split_text(text)

    combined = " ".join(chunk.text for chunk in chunks)

    assert "First paragraph" in combined
    assert "Second paragraph" in combined
    assert "Third paragraph" in combined


def test_prefers_paragraph_boundary() -> None:
    """Chunking should prefer paragraph boundaries."""
    text = "A" * 40 + "\n\n" + "B" * 40 + "\n\n" + "C" * 40

    chunker = TextChunker(
        chunk_size=90,
        chunk_overlap=10,
    )

    chunks = chunker.split_text(text)

    assert len(chunks) >= 2


def test_character_positions_are_valid() -> None:
    """Chunk character positions should refer to the source text."""
    text = "This is some document text that needs chunking."

    chunker = TextChunker(
        chunk_size=20,
        chunk_overlap=5,
    )

    chunks = chunker.split_text(text)

    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert 0 <= chunk.start_char < chunk.end_char <= len(text)


def test_invalid_chunk_size_is_rejected() -> None:
    """Non-positive chunk sizes should be rejected."""
    with pytest.raises(ValueError, match="chunk_size"):
        TextChunker(chunk_size=0)


def test_negative_overlap_is_rejected() -> None:
    """Negative overlap should be rejected."""
    with pytest.raises(ValueError, match="chunk_overlap"):
        TextChunker(
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_overlap_equal_to_chunk_size_is_rejected() -> None:
    """Overlap must be smaller than the chunk size."""
    with pytest.raises(ValueError, match="smaller"):
        TextChunker(
            chunk_size=100,
            chunk_overlap=100,
        )
