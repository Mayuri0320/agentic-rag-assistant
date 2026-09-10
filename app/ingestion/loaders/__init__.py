"""Document loader package."""

from app.ingestion.loaders.base import DocumentLoader
from app.ingestion.loaders.docx import DocxLoader
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.ingestion.loaders.pdf import PDFLoader
from app.ingestion.loaders.text import TextLoader

__all__ = [
    "DocumentLoader",
    "DocumentLoaderFactory",
    "DocxLoader",
    "PDFLoader",
    "TextLoader",
]
