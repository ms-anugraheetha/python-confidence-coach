"""
app/db/base.py — SQLAlchemy declarative base and shared mixins.

WHY THIS FILE EXISTS:
  Every SQLAlchemy model must inherit from the SAME DeclarativeBase instance.
  Using different bases in different files breaks Alembic's autogenerate —
  it silently misses models. One file, one base, no surprises.

  The mixins (UUIDMixin, TimestampMixin) encode two decisions that apply to
  every table: UUIDs as primary keys, and automatic timestamp columns.
  Rather than repeating these on every model, we inherit them.

USAGE:
  from app.db.base import Base, UUIDMixin, TimestampMixin

  class MyModel(UUIDMixin, TimestampMixin, Base):
      __tablename__ = "my_table"
      ...
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    All models must inherit from this exact instance.
    Alembic's env.py imports this to discover every table for migrations.
    """
    pass


class UUIDMixin:
    """
    Adds a UUID v4 primary key column named `id` to any model.

    WHY UUID OVER INTEGER:
      - No information leakage (integer IDs reveal user count, order, etc.)
      - Globally unique — safe to generate in Python without a DB round-trip
      - Required for distributed systems (multiple app instances, migrations)

    WHY default=uuid.uuid4 (Python-side) NOT server_default:
      For primary keys, we want Python to know the ID BEFORE the INSERT so we
      can use it in related objects without a flush. For timestamps we use
      server_default because the DB is the authority on time.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        # index=True is implicit for primary keys
    )


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` columns to any model.

    WHY server_default FOR created_at:
      The database sets this when the row is inserted, regardless of whether
      the insert came through the ORM, raw SQL, or a migration script.
      This is the correct source of truth for "when did this row appear".

    WHY onupdate=func.now() FOR updated_at:
      SQLAlchemy calls func.now() automatically on every UPDATE statement
      for this column. You never have to manually set updated_at.
      This ensures it's always accurate even on partial updates.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
