"""Database base declarative configuration and mixins."""
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime

class Base(DeclarativeBase):
    """Base model class for all SQLAlchemy ORM models."""
    pass

class TimestampMixin:
    """Reusable mixin providing created_at and updated_at tracking."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
