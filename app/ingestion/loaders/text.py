"""Plain-text document loader."""

from pathlib import Path

from app.ingestion.loaders.base import DocumentLoader


class TextLoader(DocumentLoader):
    """Load plain-text documents."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        """Return supported plain-text MIME types."""
        return frozenset({"text/plain"})

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return supported plain-text extensions."""
        return frozenset({".txt"})

    def load(self, path: Path) -> str:
        """Read and return UTF-8 text from a file."""
        return path.read_text(encoding="utf-8")
