"""Tests for JWT token creation and verification."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.auth import ALGORITHM, create_access_token, create_refresh_token, verify_token
from app.config import settings


class TestCreateAccessToken:
    def test_returns_valid_jwt(self):
        token = create_access_token("user-123")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert "exp" in payload

    def test_different_tokens_for_different_users(self):
        t1 = create_access_token("user-1")
        t2 = create_access_token("user-2")
        assert t1 != t2
        assert verify_token(t1)["sub"] == "user-1"
        assert verify_token(t2)["sub"] == "user-2"


class TestCreateRefreshToken:
    def test_includes_refresh_type(self):
        token = create_refresh_token("user-123")
        payload = verify_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user-123"

    def test_differs_from_access_token(self):
        access = create_access_token("user-123")
        refresh = create_refresh_token("user-123")
        assert access != refresh
        assert "type" not in verify_token(access)
        assert verify_token(refresh)["type"] == "refresh"


class TestVerifyToken:
    def test_valid_token(self):
        token = create_access_token("user-123")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_invalid_token_returns_none(self):
        assert verify_token("not.a.valid.token") is None
        assert verify_token("") is None

    def test_expired_token_returns_none(self):
        past = datetime.now(UTC) - timedelta(hours=1)
        token = jwt.encode(
            {"sub": "user-123", "exp": past}, settings.secret_key, algorithm=ALGORITHM,
        )
        assert verify_token(token) is None

    def test_wrong_secret_returns_none(self):
        token = jwt.encode(
            {"sub": "user-123"},
            "wrong-secret-key-that-is-at-least-32-chars-long",
            algorithm=ALGORITHM,
        )
        assert verify_token(token) is None
