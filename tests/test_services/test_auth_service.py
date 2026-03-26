"""Tests for auth service (password hashing)."""


from app.services.auth_service import hash_password, verify_password


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        hashed = hash_password("testpassword123")
        assert hashed.startswith("$2b$")
        assert hashed != "testpassword123"

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        # bcrypt uses random salt, so hashes should differ
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password(self):
        hashed = hash_password("nonempty")
        assert verify_password("", hashed) is False
