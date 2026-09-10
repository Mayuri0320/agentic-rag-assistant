"""DOCX document loader."""

from pathlib import Path

from docx import Document

from app.ingestion.loaders.base import DocumentLoader


class DocxLoader(DocumentLoader):
    """Extract text from Microsoft Word DOCX documents."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        """Return supported DOCX MIME types."""
        return frozenset(
            {
                "application/"
                "vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        )

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return supported DOCX file extensions."""
        return frozenset({".docx"})

    def load(self, path: Path) -> str:
        """Extract text from paragraphs in a DOCX document."""
        document = Document(str(path))

        paragraphs = [
            paragraph.text for paragraph in document.paragraphs if paragraph.text
        ]

        return "\n\n".join(paragraphs)
