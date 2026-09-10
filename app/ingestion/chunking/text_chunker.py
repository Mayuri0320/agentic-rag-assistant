"""Text chunking utilities for the RAG ingestion pipeline."""

from app.ingestion.chunking.models import DocumentChunk


class TextChunker:
    """Split cleaned document text into overlapping chunks."""

    def __init__(
        self,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """Initialize the text chunker."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[DocumentChunk]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []

        chunks: list[DocumentChunk] = []

        start = 0
        text_length = len(text)
        chunk_index = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            if end < text_length:
                boundary = self._find_boundary(
                    text=text,
                    start=start,
                    end=end,
                )

                if boundary > start:
                    end = boundary

            chunk_text = text[start:end].strip()

            if chunk_text:
                actual_start = start + (
                    len(text[start:end]) - len(text[start:end].lstrip())
                )
                actual_end = actual_start + len(chunk_text)

                chunks.append(
                    DocumentChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        start_char=actual_start,
                        end_char=actual_end,
                    )
                )

                chunk_index += 1

            if end >= text_length:
                break

            next_start = max(end - self.chunk_overlap, start + 1)

            start = next_start

        return chunks

    def _find_boundary(
        self,
        *,
        text: str,
        start: int,
        end: int,
    ) -> int:
        """Find a natural boundary near the requested chunk size."""
        minimum_boundary = start + (self.chunk_size // 2)

        paragraph_boundary = text.rfind("\n\n", minimum_boundary, end)

        if paragraph_boundary != -1:
            return paragraph_boundary

        sentence_boundaries = (
            text.rfind(". ", minimum_boundary, end),
            text.rfind("? ", minimum_boundary, end),
            text.rfind("! ", minimum_boundary, end),
        )

        sentence_boundary = max(sentence_boundaries)

        if sentence_boundary != -1:
            return sentence_boundary + 1

        whitespace_boundary = text.rfind(" ", minimum_boundary, end)

        if whitespace_boundary != -1:
            return whitespace_boundary

        return end
