"""Health response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
    database: bool
    redis: bool
