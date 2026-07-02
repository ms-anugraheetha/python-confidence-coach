"""
app/db/repositories/user_repo.py — UserRepository.

WHY A REPOSITORY:
  All SQL lives here. Routes never import sqlalchemy directly.
  If we switch from SQLAlchemy to something else later, only this file changes.

  Every method takes an AsyncSession as first arg (after self).
  The session is provided by the get_db() FastAPI dependency.
  The repo never commits or rolls back — that's the dependency's job.

PATTERN:
  repo = UserRepository()
  user = await repo.get_by_email(db, email)
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    """Data access layer for the users table."""

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key. Returns None if not found."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Fetch a user by email (case-insensitive).
        Used for login and "already registered" checks.
        """
        result = await db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        display_name: str = "Learner",
    ) -> User:
        """
        Insert a new user row.

        Caller is responsible for hashing the password before passing it here.
        The session is flushed so the user's id is available immediately,
        but NOT committed — commit happens in get_db() after the route returns.
        """
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed_password,
            display_name=display_name,
        )
        db.add(user)
        await db.flush()   # Assigns DB-generated defaults (id, created_at) immediately
        await db.refresh(user)  # Loads the server-side defaults back into the ORM object
        return user

    async def update_display_name(
        self,
        db: AsyncSession,
        user: User,
        display_name: str,
    ) -> User:
        """Update a user's display name in place."""
        user.display_name = display_name
        await db.flush()
        await db.refresh(user)
        return user

    async def exists_by_email(self, db: AsyncSession, email: str) -> bool:
        """
        Returns True if an account with this email exists.
        Cheaper than get_by_email because we don't hydrate the full object.
        Used during registration to give a fast 409 before attempting the insert.
        """
        result = await db.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None


# Module-level singleton — instantiated once, shared everywhere via DI.
user_repo = UserRepository()
