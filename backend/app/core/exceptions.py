"""
app/core/exceptions.py — Application exception hierarchy.

WHY THIS FILE EXISTS:
  Services raise domain exceptions (NotFoundError, AuthenticationError).
  They don't know about HTTP — that's the route layer's concern.
  The exception handlers in main.py translate domain exceptions → HTTP responses.

  This gives you:
    - Clean service code that raises meaningful errors
    - A single place to map errors to HTTP status codes
    - Consistent JSON error responses that the frontend can always rely on
    - Easy testing: assert the right exception was raised, not the HTTP code

HIERARCHY:
  AppError                 (base — catches all app errors)
  ├── AuthenticationError  (401 — invalid or missing credentials)
  ├── AuthorizationError   (403 — authenticated but not permitted)
  ├── NotFoundError        (404 — resource doesn't exist)
  ├── ConflictError        (409 — resource already exists)
  ├── ValidationError      (422 — business-rule validation, not Pydantic schema)
  ├── MCPError             (502 — MCP server call failed)
  └── ExternalServiceError (502 — other external service failed)

USAGE (in a service):
  from app.core.exceptions import NotFoundError
  raise NotFoundError("User", user_id)

USAGE (in a route — you don't need to catch these):
  The handlers in main.py catch AppError subclasses automatically.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ── Error response schema ─────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """
    The JSON body returned for every error response.

    The frontend always receives this shape, regardless of which error occurred.
    This means the frontend only needs one error-parsing function.

    Example:
        {
            "code": "NOT_FOUND",
            "message": "User with id 42 was not found.",
            "details": {}
        }
    """
    code: str
    message: str
    details: dict[str, Any] = {}


# ── Base exception ────────────────────────────────────────────────────────────

class AppError(Exception):
    """
    Base class for all application exceptions.

    Every domain exception inherits from this. Catch `AppError` to handle
    any application-level error, or catch specific subclasses for targeted handling.

    Attributes:
        message:     Human-readable description. Goes in the JSON response body.
        code:        Machine-readable error code. Used by the frontend for i18n
                     or to decide which UI element to highlight.
        http_status: The HTTP status code to return to the client.
        details:     Optional extra context (field names, resource IDs, etc.)
    """

    message: str
    code: str
    http_status: int
    details: dict[str, Any]

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Serialise to the standard ErrorResponse for JSON output."""
        return ErrorResponse(
            code=self.code,
            message=self.message,
            details=self.details,
        )


# ── Authentication (401) ──────────────────────────────────────────────────────

class AuthenticationError(AppError):
    """
    Raised when credentials are missing, invalid, or expired.
    Maps to HTTP 401 Unauthorized.

    Examples:
        - JWT token missing from Authorization header
        - JWT token signature invalid
        - JWT token expired
        - Password does not match hash
    """
    http_status = 401

    def __init__(
        self,
        message: str = "Authentication required.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR", details=details)


class TokenExpiredError(AuthenticationError):
    """JWT access token has expired. Client should use the refresh token."""
    def __init__(self) -> None:
        super().__init__(
            message="Your session has expired. Please log in again.",
            details={"reason": "token_expired"},
        )


class InvalidTokenError(AuthenticationError):
    """JWT token is present but cannot be decoded or verified."""
    def __init__(self) -> None:
        super().__init__(
            message="Invalid authentication token.",
            details={"reason": "token_invalid"},
        )


# ── Authorization (403) ───────────────────────────────────────────────────────

class AuthorizationError(AppError):
    """
    Raised when a user is authenticated but lacks permission for the action.
    Maps to HTTP 403 Forbidden.

    Note the difference from AuthenticationError:
        401 = "I don't know who you are."
        403 = "I know who you are, but you can't do this."
    """
    http_status = 403

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR", details=details)


# ── Not Found (404) ───────────────────────────────────────────────────────────

class NotFoundError(AppError):
    """
    Raised when a requested resource does not exist.
    Maps to HTTP 404 Not Found.

    Usage:
        raise NotFoundError("User", user_id)
        # → "User with id '42' was not found."

        raise NotFoundError("Conversation", conversation_id)
        # → "Conversation with id 'abc-123' was not found."
    """
    http_status = 404

    def __init__(
        self,
        resource: str,
        identifier: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{resource} with id '{identifier}' was not found.",
            code="NOT_FOUND",
            details=details or {"resource": resource, "id": str(identifier)},
        )


# ── Conflict (409) ────────────────────────────────────────────────────────────

class ConflictError(AppError):
    """
    Raised when a resource already exists and cannot be created again.
    Maps to HTTP 409 Conflict.

    Usage:
        raise ConflictError("User", "email", email)
        # → "User with email 'alice@example.com' already exists."
    """
    http_status = 409

    def __init__(
        self,
        resource: str,
        field: str,
        value: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists.",
            code="CONFLICT",
            details=details or {"resource": resource, "field": field, "value": str(value)},
        )


# ── Validation (422) ──────────────────────────────────────────────────────────

class ValidationError(AppError):
    """
    Raised when business-rule validation fails (not Pydantic schema validation).
    Maps to HTTP 422 Unprocessable Entity.

    This is for domain rules, NOT for missing/wrong-type fields.
    Pydantic handles schema validation automatically — this is for things like:
        "A conversation cannot have more than 100 messages."
        "Password must contain at least one number."

    Pydantic's own ValidationError is a different class (pydantic.ValidationError)
    and is handled separately in main.py.
    """
    http_status = 422

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra = details or {}
        if field:
            extra["field"] = field
        super().__init__(message=message, code="VALIDATION_ERROR", details=extra)


# ── External services (502) ───────────────────────────────────────────────────

class MCPError(AppError):
    """
    Raised when a call to the MCP server fails.
    Maps to HTTP 502 Bad Gateway.

    Usage:
        raise MCPError("explain_concept", "Connection refused")
    """
    http_status = 502

    def __init__(
        self,
        tool_name: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"MCP tool '{tool_name}' failed: {reason}",
            code="MCP_ERROR",
            details=details or {"tool": tool_name, "reason": reason},
        )


class ExternalServiceError(AppError):
    """
    Raised when any external service (Anthropic API, etc.) is unavailable.
    Maps to HTTP 502 Bad Gateway.
    """
    http_status = 502

    def __init__(
        self,
        service: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"External service '{service}' is unavailable: {reason}",
            code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service, "reason": reason},
        )
