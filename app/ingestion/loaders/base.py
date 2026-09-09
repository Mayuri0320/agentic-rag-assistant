"""Base abstractions for document loaders."""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentLoader(ABC):
    """Abstract interface for document loaders."""

    @property
    @abstractmethod
    def supported_mime_types(self) -> frozenset[str]:
        """Return MIME types supported by this loader."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_extensions(self) -> frozenset[str]:
        """Return file extensions supported by this loader."""
        raise NotImplementedError

    @abstractmethod
    def load(self, path: Path) -> str:
        """Extract and return text from a document."""
        raise NotImplementedError
