"""Tests for the username utility function."""

from app.utils.username import default_username_from_email


class TestDefaultUsernameFromEmail:
    """Test the default_username_from_email utility."""

    def test_normal_email_returns_local_part(self):
        assert default_username_from_email("alice@example.com") == "alice"

    def test_local_part_longer_than_max_length_is_truncated(self):
        long_local = "a" * 100
        result = default_username_from_email(f"{long_local}@example.com")
        assert result == "a" * 64
        assert len(result) <= 64

    def test_short_local_part_padded_with_user(self):
        # "ab" is length 2, below default min_length of 3
        result = default_username_from_email("ab@example.com")
        assert len(result) >= 3
        assert result.startswith("ab")

    def test_single_char_local_part_padded(self):
        result = default_username_from_email("x@example.com")
        assert len(result) >= 3

    def test_empty_local_part_falls_back_to_user(self):
        # email starting with @
        result = default_username_from_email("@example.com")
        assert len(result) >= 3
        assert result == "user"

    def test_local_part_exactly_min_length(self):
        result = default_username_from_email("abc@example.com")
        assert result == "abc"

    def test_custom_max_length(self):
        result = default_username_from_email("verylongname@example.com", max_length=5)
        assert len(result) <= 5

    def test_custom_min_length(self):
        result = default_username_from_email("ab@example.com", min_length=5)
        assert len(result) >= 5

    def test_local_part_with_dots_and_plus(self):
        result = default_username_from_email("first.last+tag@example.com")
        assert result == "first.last+tag"

    def test_whitespace_stripped_from_local_part(self):
        # email with leading/trailing whitespace around local part (after split)
        result = default_username_from_email(" spaces @example.com")
        assert not result.startswith(" ")
        assert not result.endswith(" ")
        assert len(result) >= 3

    def test_result_never_exceeds_max_length(self):
        # Even when padding is needed, result should respect max_length
        result = default_username_from_email("a@example.com", max_length=4, min_length=3)
        assert len(result) <= 4

    def test_no_at_sign_uses_entire_string_as_local_part(self):
        # email.split("@")[0] on a string without @ returns the whole string
        result = default_username_from_email("nodomain")
        assert result == "nodomain"

    def test_returns_string(self):
        result = default_username_from_email("test@example.com")
        assert isinstance(result, str)
