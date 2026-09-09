"""SQLAlchemy declarative base."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Import models so SQLAlchemy registers them with Base.metadata.
# from app.db.models.document import Document  # noqa: E402,F401
# from app.db.models.user import User  # noqa: E402,F401
