"""Text cleaning and normalization utilities."""

import re
import unicodedata


class TextCleaner:
    """Clean and normalize extracted document text."""

    _MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
    _MULTIPLE_SPACES = re.compile(r"[ \t]{2,}")
    _SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([,.;:!?])")
    _BROKEN_HYPHENATION = re.compile(r"(\w)-\n(\w)")

    def clean(self, text: str) -> str:
        """Normalize and clean extracted text."""
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = self._remove_control_characters(text)
        text = self._BROKEN_HYPHENATION.sub(r"\1\2", text)
        text = self._SPACE_BEFORE_PUNCTUATION.sub(r"\1", text)
        text = self._MULTIPLE_SPACES.sub(" ", text)
        text = self._MULTIPLE_NEWLINES.sub("\n\n", text)

        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()

    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """Remove unwanted Unicode control characters."""
        return "".join(
            character
            for character in text
            if character in "\n\t"
            or not unicodedata.category(character).startswith("C")
        )
