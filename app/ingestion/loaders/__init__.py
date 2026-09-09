"""Document loader package."""

from app.ingestion.loaders.base import DocumentLoader
from app.ingestion.loaders.factory import DocumentLoaderFactory

__all__ = [
    "DocumentLoader",
    "DocumentLoaderFactory",
]
