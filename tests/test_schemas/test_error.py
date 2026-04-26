"""Tests for error schemas."""

from app.schemas.error import (
    ErrorCode,
    ErrorResponse,
    build_error_example,
    error_response,
    error_response_dict,
    error_response_doc,
    success_response_doc,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_values(self):
        """Test that all expected error codes exist."""
        assert ErrorCode.INVALID_CREDENTIALS.value == "INVALID_CREDENTIALS"
        assert ErrorCode.TOKEN_EXPIRED.value == "TOKEN_EXPIRED"
        assert ErrorCode.TOKEN_INVALID.value == "TOKEN_INVALID"
        assert ErrorCode.REFRESH_TOKEN_REQUIRED.value == "REFRESH_TOKEN_REQUIRED"
        assert ErrorCode.USER_INACTIVE.value == "USER_INACTIVE"
        assert ErrorCode.USER_ALREADY_EXISTS.value == "USER_ALREADY_EXISTS"
        assert ErrorCode.FORBIDDEN.value == "FORBIDDEN"
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert ErrorCode.RESOURCE_CONFLICT.value == "RESOURCE_CONFLICT"
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.INVALID_FORMAT.value == "INVALID_FORMAT"
        assert ErrorCode.RATE_LIMIT_EXCEEDED.value == "RATE_LIMIT_EXCEEDED"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
        assert ErrorCode.SERVICE_UNAVAILABLE.value == "SERVICE_UNAVAILABLE"

    def test_error_code_is_enum(self):
        """Test that ErrorCode is a proper enum."""
        from enum import Enum

        assert issubclass(ErrorCode, Enum)


class TestBuildErrorExample:
    """Tests for build_error_example function."""

    def test_build_error_example_with_error_code_enum(self):
        """Test build_error_example with ErrorCode enum."""
        result = build_error_example(
            ErrorCode.NOT_FOUND,
            "Resource not found",
            {"resource_id": "123"},
        )

        assert result == {
            "error": {"code": "NOT_FOUND", "message": "Resource not found"},
            "details": {"resource_id": "123"},
        }

    def test_build_error_example_with_string_code(self):
        """Test build_error_example with string error code."""
        result = build_error_example("INVALID_CREDENTIALS", "Invalid credentials")

        assert result == {
            "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"},
            "details": None,
        }

    def test_build_error_example_without_details(self):
        """Test build_error_example without details."""
        result = build_error_example(ErrorCode.INTERNAL_ERROR, "Internal error")

        assert result == {
            "error": {"code": "INTERNAL_ERROR", "message": "Internal error"},
            "details": None,
        }


class TestErrorResponseDoc:
    """Tests for error_response_doc function."""

    def test_error_response_doc_structure(self):
        """Test error_response_doc returns proper OpenAPI structure."""
        result = error_response_doc(
            description="Not found",
            code=ErrorCode.NOT_FOUND,
            message="Resource not found",
        )

        assert result["model"] == ErrorResponse
        assert result["description"] == "Not found"
        assert "application/json" in result["content"]
        assert result["content"]["application/json"]["example"]["error"]["code"] == "NOT_FOUND"

    def test_error_response_doc_with_details(self):
        """Test error_response_doc with details."""
        result = error_response_doc(
            description="Validation error",
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input",
            details={"field": "email"},
        )

        assert result["content"]["application/json"]["example"]["details"] == {"field": "email"}


class TestSuccessResponseDoc:
    """Tests for success_response_doc function."""

    def test_success_response_doc_structure(self):
        """Test success_response_doc returns proper OpenAPI structure."""
        example = {"id": "123", "name": "test"}
        result = success_response_doc(description="Success", example=example)

        assert result["description"] == "Success"
        assert result["content"]["application/json"]["example"] == example


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response_create(self):
        """Test creating an ErrorResponse."""
        response = ErrorResponse(
            error={"code": "NOT_FOUND", "message": "Not found"},
            details={"id": "123"},
        )

        assert response.error["code"] == "NOT_FOUND"
        assert response.details == {"id": "123"}

    def test_error_response_without_details(self):
        """Test ErrorResponse without details."""
        response = ErrorResponse(error={"code": "ERROR", "message": "msg"})

        assert response.details is None


class TestErrorResponseHelper:
    """Tests for error_response helper function."""

    def test_error_response_helper(self):
        """Test error_response helper creates proper ErrorResponse."""
        result = error_response(
            ErrorCode.NOT_FOUND,
            "Resource not found",
            {"job_id": "abc"},
        )

        assert isinstance(result, ErrorResponse)
        assert result.error["code"] == "NOT_FOUND"
        assert result.error["message"] == "Resource not found"
        assert result.details == {"job_id": "abc"}

    def test_error_response_helper_without_details(self):
        """Test error_response helper without details."""
        result = error_response(ErrorCode.INTERNAL_ERROR, "Internal error")

        assert isinstance(result, ErrorResponse)
        assert result.error["code"] == "INTERNAL_ERROR"
        assert result.details is None


class TestErrorResponseDictHelper:
    """Tests for error_response_dict helper function."""

    def test_error_response_dict_helper(self):
        """Test error_response_dict helper creates dict directly."""
        result = error_response_dict(
            ErrorCode.FORBIDDEN,
            "Access denied",
            {"resource": "file.txt"},
        )

        assert isinstance(result, dict)
        assert not isinstance(result, ErrorResponse)
        assert result == {
            "error": {"code": "FORBIDDEN", "message": "Access denied"},
            "details": {"resource": "file.txt"},
        }

    def test_error_response_dict_helper_without_details(self):
        """Test error_response_dict helper without details."""
        result = error_response_dict(ErrorCode.UNAUTHORIZED, "Unauthorized")

        assert result == {
            "error": {"code": "UNAUTHORIZED", "message": "Unauthorized"},
            "details": None,
        }
