"""Tests for the document loader factory."""

from pathlib import Path

import pytest

from app.ingestion.exceptions import UnsupportedDocumentTypeError
from app.ingestion.loaders.base import DocumentLoader
from app.ingestion.loaders.factory import DocumentLoaderFactory


class FakePDFLoader(DocumentLoader):
    """Fake PDF loader used for factory tests."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        """Return supported PDF MIME types."""
        return frozenset({"application/pdf"})

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return supported PDF extensions."""
        return frozenset({".pdf"})

    def load(self, path: Path) -> str:
        """Return fake extracted text."""
        return f"PDF: {path.name}"


class FakeTextLoader(DocumentLoader):
    """Fake text loader used for factory tests."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        """Return supported text MIME types."""
        return frozenset({"text/plain"})

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return supported text extensions."""
        return frozenset({".txt"})

    def load(self, path: Path) -> str:
        """Return fake extracted text."""
        return f"TEXT: {path.name}"


class FakeDocxLoader(DocumentLoader):
    """Fake DOCX loader used for factory tests."""

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
        """Return supported DOCX extensions."""
        return frozenset({".docx"})

    def load(self, path: Path) -> str:
        """Return fake extracted text."""
        return f"DOCX: {path.name}"


@pytest.fixture
def factory() -> DocumentLoaderFactory:
    """Create a factory containing all fake loaders."""
    return DocumentLoaderFactory(
        loaders=[
            FakePDFLoader(),
            FakeTextLoader(),
            FakeDocxLoader(),
        ]
    )


def test_factory_returns_pdf_loader(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should select the PDF loader."""
    loader = factory.get_loader(
        file_type="application/pdf",
        filename="report.pdf",
    )

    assert isinstance(loader, FakePDFLoader)


def test_factory_returns_text_loader(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should select the text loader."""
    loader = factory.get_loader(
        file_type="text/plain",
        filename="notes.txt",
    )

    assert isinstance(loader, FakeTextLoader)


def test_factory_returns_docx_loader(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should select the DOCX loader."""
    loader = factory.get_loader(
        file_type=(
            "application/" "vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename="paper.docx",
    )

    assert isinstance(loader, FakeDocxLoader)


def test_factory_normalizes_mime_type(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should normalize MIME type parameters and casing."""
    loader = factory.get_loader(
        file_type="Application/PDF; charset=binary",
        filename="report.pdf",
    )

    assert isinstance(loader, FakePDFLoader)


def test_factory_falls_back_to_extension(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should use the filename extension as a fallback."""
    loader = factory.get_loader(
        file_type="application/octet-stream",
        filename="report.pdf",
    )

    assert isinstance(loader, FakePDFLoader)


def test_factory_rejects_unsupported_type(
    factory: DocumentLoaderFactory,
) -> None:
    """Factory should reject unsupported document types."""
    with pytest.raises(UnsupportedDocumentTypeError):
        factory.get_loader(
            file_type="image/png",
            filename="image.png",
        )
