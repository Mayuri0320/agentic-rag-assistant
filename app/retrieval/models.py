"""Models used by the retrieval layer."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A single semantically retrieved document chunk."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float | None
