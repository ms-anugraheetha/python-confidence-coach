"""app/api/v1/routes/auth.py — Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.repositories.user_repo import user_repo
from app.db.session import get_db

router = APIRouter(prefix="/auth")

_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/api/v1/auth")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    if await user_repo.exists_by_email(db, data.email):
        raise ConflictError("User", "email", data.email)

    user = await user_repo.create(
        db,
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name or "Learner",
    )
    _set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await user_repo.get_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    _set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
) -> TokenResponse:
    if not refresh_token:
        raise AuthenticationError("No refresh token.")

    user_id = decode_refresh_token(refresh_token)
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        _clear_refresh_cookie(response)
        raise AuthenticationError("User not found.")

    _set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout")
async def logout(response: Response) -> dict:
    _clear_refresh_cookie(response)
    return {"message": "Logged out."}


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[object, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(user)
