"""Document file storage."""

from pathlib import Path
from uuid import uuid4


class DocumentStorage:
    """Store uploaded document files on the local filesystem."""

    def __init__(self, base_directory: str) -> None:
        """Initialize document storage."""
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        filename: str,
        content: bytes,
    ) -> str:
        """Save a document and return its storage path."""
        extension = Path(filename).suffix.lower()
        stored_filename = f"{uuid4().hex}{extension}"

        file_path = self.base_directory / stored_filename
        file_path.write_bytes(content)

        return str(file_path)

    def delete(self, storage_path: str) -> None:
        """Delete a stored document if it exists."""
        file_path = Path(storage_path)

        if file_path.exists():
            file_path.unlink()
