"""PDF document loader."""

from pathlib import Path

from pypdf import PdfReader

from app.ingestion.loaders.base import DocumentLoader


class PDFLoader(DocumentLoader):
    """Extract text from PDF documents."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        """Return supported PDF MIME types."""
        return frozenset({"application/pdf"})

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return supported PDF file extensions."""
        return frozenset({".pdf"})

    def load(self, path: Path) -> str:
        """Extract text from all pages in a PDF."""
        reader = PdfReader(path)

        pages: list[str] = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)
