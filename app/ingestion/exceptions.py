"""Exceptions raised by the document ingestion system."""


class UnsupportedDocumentTypeError(ValueError):
    """Raised when no document loader supports the requested file type."""

    def __init__(self, file_type: str, filename: str) -> None:
        self.file_type = file_type
        self.filename = filename

        super().__init__(
            f"Unsupported document type: "
            f"file_type={file_type!r}, filename={filename!r}"
        )
