"""Models used by the embedding pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    """Represent a document chunk together with its embedding."""

    text: str
    embedding: list[float]
    chunk_index: int
