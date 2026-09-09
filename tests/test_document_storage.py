"""Tests for document storage."""

from pathlib import Path

from app.storage.document_storage import DocumentStorage


def test_save_document(tmp_path: Path) -> None:
    """A document should be saved to storage."""
    storage = DocumentStorage(str(tmp_path))

    storage_path = storage.save(
        filename="report.pdf",
        content=b"test document",
    )

    saved_file = Path(storage_path)

    assert saved_file.exists()
    assert saved_file.read_bytes() == b"test document"
    assert saved_file.suffix == ".pdf"


def test_save_generates_unique_filename(tmp_path: Path) -> None:
    """Stored filenames should be unique."""
    storage = DocumentStorage(str(tmp_path))

    first = storage.save(
        filename="report.pdf",
        content=b"first",
    )

    second = storage.save(
        filename="report.pdf",
        content=b"second",
    )

    assert first != second


def test_delete_document(tmp_path: Path) -> None:
    """A stored document should be deleted."""
    storage = DocumentStorage(str(tmp_path))

    storage_path = storage.save(
        filename="report.pdf",
        content=b"test document",
    )

    assert Path(storage_path).exists()

    storage.delete(storage_path)

    assert not Path(storage_path).exists()


def test_delete_missing_document(tmp_path: Path) -> None:
    """Deleting a missing document should not fail."""
    storage = DocumentStorage(str(tmp_path))

    storage.delete(
        str(tmp_path / "does-not-exist.pdf"),
    )
