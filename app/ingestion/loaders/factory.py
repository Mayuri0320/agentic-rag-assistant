"""Factory for selecting document loaders."""

from collections.abc import Sequence
from pathlib import Path

from app.ingestion.exceptions import UnsupportedDocumentTypeError
from app.ingestion.loaders.base import DocumentLoader


class DocumentLoaderFactory:
    """Select the appropriate document loader for an uploaded file."""

    def __init__(self, loaders: Sequence[DocumentLoader]) -> None:
        """Initialize the factory with available loaders."""
        self._loaders = tuple(loaders)

    def get_loader(
        self,
        *,
        file_type: str,
        filename: str,
    ) -> DocumentLoader:
        """Return the loader capable of processing the requested document."""
        normalized_file_type = self._normalize_file_type(file_type)
        extension = Path(filename).suffix.lower()

        for loader in self._loaders:
            if normalized_file_type in loader.supported_mime_types:
                return loader

        for loader in self._loaders:
            if extension in loader.supported_extensions:
                return loader

        raise UnsupportedDocumentTypeError(
            file_type=file_type,
            filename=filename,
        )

    @staticmethod
    def _normalize_file_type(file_type: str) -> str:
        """Normalize a MIME type before comparing it."""
        return file_type.split(";", maxsplit=1)[0].strip().lower()
