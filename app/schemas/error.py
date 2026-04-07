"""Standardized error response schemas."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ErrorCode(Enum):
    """Standard error codes for the API."""

    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    REFRESH_TOKEN_REQUIRED = "REFRESH_TOKEN_REQUIRED"
    USER_INACTIVE = "USER_INACTIVE"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"

    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    UNAUTHORIZED = "UNAUTHORIZED"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# Type alias for error codes that can be serialized as strings
ErrorCodeType = Literal[
    "INVALID_CREDENTIALS",
    "TOKEN_EXPIRED",
    "TOKEN_INVALID",
    "REFRESH_TOKEN_REQUIRED",
    "USER_INACTIVE",
    "USER_ALREADY_EXISTS",
    "FORBIDDEN",
    "UNAUTHORIZED",
    "NOT_FOUND",
    "RESOURCE_CONFLICT",
    "VALIDATION_ERROR",
    "INVALID_FORMAT",
    "RATE_LIMIT_EXCEEDED",
    "INTERNAL_ERROR",
    "SERVICE_UNAVAILABLE",
]


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {"code": "NOT_FOUND", "message": "Resource not found"},
                "details": {"job_id": "123"},
            },
        },
    )

    error: dict[str, str]
    details: dict[str, Any] | None = None


def build_error_example(
    code: ErrorCode | ErrorCodeType,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized OpenAPI error example payload."""
    code_value = code.value if isinstance(code, ErrorCode) else code
    return {
        "error": {"code": code_value, "message": message},
        "details": details,
    }


def error_response_doc(
    description: str,
    code: ErrorCode | ErrorCodeType,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an OpenAPI response object for standardized error payloads."""
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": build_error_example(code, message, details),
            },
        },
    }


def success_response_doc(description: str, example: dict[str, Any]) -> dict[str, Any]:
    """Build an OpenAPI response object for success payloads."""
    return {
        "description": description,
        "content": {"application/json": {"example": example}},
    }


def error_response(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> ErrorResponse:
    """Helper to create a standardized error response."""
    return ErrorResponse(
        error={"code": code.value, "message": message},
        details=details,
    )


def error_response_dict(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict:
    """Helper to create a standardized error response dict."""
    return {
        "error": {"code": code.value, "message": message},
        "details": details,
    }
