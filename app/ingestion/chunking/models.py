"""Models used by the document chunking pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """Represent a chunk of extracted document text."""

    text: str
    chunk_index: int
    start_char: int
    end_char: int
