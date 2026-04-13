"""Tests for the registration page password strength indicator and related changes.

Covers:
- Password strength HTML elements present in the rendered register page
- Updated password hint text
- CSRF token meta tag in base template
- htmx:configRequest event listener in base template
- Password strength JavaScript logic (evaluatePasswordStrength) ported to Python
  to verify classification rules exhaustively
"""

import re

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _evaluate_password_strength(password: str) -> dict:
    """Python port of the evaluatePasswordStrength JS function from register.html.

    Mirrors the exact logic so we can test all branches without a browser.
    """
    has_minimum_length = len(password) >= 8
    has_number = bool(re.search(r"\d", password))
    has_special_character = bool(re.search(r"[^A-Za-z0-9]", password))
    checks_passed = sum([has_minimum_length, has_number, has_special_character])

    if len(password) == 0:
        return {"levelClass": "", "label": "Start typing to check password strength"}

    if checks_passed == 3:
        return {"levelClass": "is-strong", "label": "Strong password"}

    if checks_passed == 2:
        return {"levelClass": "is-medium", "label": "Medium strength password"}

    return {"levelClass": "is-weak", "label": "Weak password"}


# ---------------------------------------------------------------------------
# Register page HTML structure tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_page_returns_200():
    """GET /web/register returns HTTP 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_page_has_password_strength_container():
    """Register page includes the password-strength container with aria-live."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    # Container must be present with aria-live="polite" for screen-reader announcements
    assert 'class="mt-3 password-strength"' in html
    assert 'aria-live="polite"' in html


@pytest.mark.asyncio
async def test_register_page_has_strength_meter_element():
    """Register page includes the password-strength-meter bar wrapper."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert 'class="password-strength-meter"' in html
    assert 'role="presentation"' in html
    assert 'aria-hidden="true"' in html


@pytest.mark.asyncio
async def test_register_page_has_strength_fill_element():
    """Register page includes the #password-strength-fill div."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert 'id="password-strength-fill"' in html
    assert 'class="password-strength-fill"' in html


@pytest.mark.asyncio
async def test_register_page_has_strength_text_element():
    """Register page includes the #password-strength-text paragraph."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert 'id="password-strength-text"' in html
    assert "Start typing to check password strength" in html


@pytest.mark.asyncio
async def test_register_page_password_hint_mentions_number_and_special():
    """Updated hint text mentions number and special character requirements."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert "one number" in html
    assert "special character" in html


@pytest.mark.asyncio
async def test_register_page_includes_password_strength_script():
    """Register page embeds the evaluatePasswordStrength JavaScript function."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert "evaluatePasswordStrength" in html
    assert "updatePasswordStrength" in html
    assert 'passwordInput.addEventListener("input", updatePasswordStrength)' in html


@pytest.mark.asyncio
async def test_register_page_script_checks_minimum_length():
    """The embedded script checks for minimum 8-character length."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert "password.length >= 8" in html


@pytest.mark.asyncio
async def test_register_page_script_checks_digit():
    """The embedded script checks for at least one digit."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert r"/\d/" in html


@pytest.mark.asyncio
async def test_register_page_script_checks_special_character():
    """The embedded script checks for at least one special character."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert r"/[^A-Za-z0-9]/" in html


# ---------------------------------------------------------------------------
# Base template CSRF / htmx changes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_page_has_csrf_meta_tag():
    """Base template renders a csrf-token meta tag on the register page."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert 'name="csrf-token"' in html


@pytest.mark.asyncio
async def test_register_page_uses_htmx_config_request_event():
    """Base template uses the htmx:configRequest event to inject CSRF header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    assert "htmx:configRequest" in html
    assert 'evt.detail.headers["X-CSRF-Token"]' in html


@pytest.mark.asyncio
async def test_register_page_does_not_use_static_htmx_config_headers():
    """The old static htmx.config.headers approach is no longer used."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    html = response.text
    # The new approach uses the event listener; the old assignment should be absent
    assert "htmx.config.headers" not in html


@pytest.mark.asyncio
async def test_csrf_cookie_set_on_register_page():
    """A csrf_token cookie is set when visiting the register page."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/web/register")

    assert "csrf_token" in response.cookies


# ---------------------------------------------------------------------------
# evaluatePasswordStrength logic tests (Python port)
# ---------------------------------------------------------------------------


class TestEvaluatePasswordStrength:
    """Test the password strength classification logic ported from register.html JS."""

    # --- empty input ---

    def test_empty_string_returns_empty_level(self):
        result = _evaluate_password_strength("")
        assert result["levelClass"] == ""

    def test_empty_string_returns_prompt_label(self):
        result = _evaluate_password_strength("")
        assert result["label"] == "Start typing to check password strength"

    # --- weak passwords (0 or 1 check passed) ---

    def test_single_letter_is_weak(self):
        result = _evaluate_password_strength("a")
        assert result["levelClass"] == "is-weak"
        assert result["label"] == "Weak password"

    def test_short_letters_only_is_weak(self):
        # Length < 8, no number, no special: 0 checks → weak
        result = _evaluate_password_strength("abc")
        assert result["levelClass"] == "is-weak"

    def test_exactly_one_check_length_only_is_weak(self):
        # Length >= 8, no number, no special: 1 check → weak
        result = _evaluate_password_strength("abcdefgh")
        assert result["levelClass"] == "is-weak"

    def test_exactly_one_check_number_only_is_weak(self):
        # Has number, length < 8, no special: 1 check → weak
        result = _evaluate_password_strength("abc1")
        assert result["levelClass"] == "is-weak"

    def test_exactly_one_check_special_only_is_weak(self):
        # Has special, length < 8, no number: 1 check → weak
        result = _evaluate_password_strength("abc!")
        assert result["levelClass"] == "is-weak"

    def test_no_checks_passed_is_weak(self):
        # Very short, letters only
        result = _evaluate_password_strength("x")
        assert result["levelClass"] == "is-weak"

    # --- medium passwords (exactly 2 checks passed) ---

    def test_length_and_number_is_medium(self):
        # Length >= 8 AND has number, no special: 2 checks → medium
        result = _evaluate_password_strength("password1")
        assert result["levelClass"] == "is-medium"
        assert result["label"] == "Medium strength password"

    def test_length_and_special_is_medium(self):
        # Length >= 8 AND has special, no number: 2 checks → medium
        result = _evaluate_password_strength("password!")
        assert result["levelClass"] == "is-medium"

    def test_number_and_special_without_length_is_medium(self):
        # Has number AND special, length < 8: 2 checks → medium
        result = _evaluate_password_strength("a1!")
        assert result["levelClass"] == "is-medium"

    def test_exactly_8_chars_with_number_is_medium(self):
        result = _evaluate_password_strength("abcdefg1")
        assert result["levelClass"] == "is-medium"

    def test_exactly_8_chars_with_special_is_medium(self):
        result = _evaluate_password_strength("abcdefg!")
        assert result["levelClass"] == "is-medium"

    # --- strong passwords (all 3 checks passed) ---

    def test_all_three_checks_is_strong(self):
        # Length >= 8, has number, has special: 3 checks → strong
        result = _evaluate_password_strength("Password1!")
        assert result["levelClass"] == "is-strong"
        assert result["label"] == "Strong password"

    def test_long_mixed_password_is_strong(self):
        result = _evaluate_password_strength("MyS3cur3P@ss!")
        assert result["levelClass"] == "is-strong"

    def test_exactly_8_chars_all_criteria_is_strong(self):
        # Exactly 8 chars, includes number and special
        result = _evaluate_password_strength("abcd1@!e")
        assert result["levelClass"] == "is-strong"

    def test_multiple_specials_and_numbers_is_strong(self):
        result = _evaluate_password_strength("a1!b2@c3#")
        assert result["levelClass"] == "is-strong"

    # --- boundary / edge cases ---

    def test_7_chars_with_number_and_special_is_medium(self):
        # 7 chars (< 8) + number + special = 2 checks → medium
        result = _evaluate_password_strength("abc1!de")
        assert result["levelClass"] == "is-medium"

    def test_8_chars_only_numbers_is_medium(self):
        # Length >= 8 AND has number, no special: 2 checks → medium
        result = _evaluate_password_strength("12345678")
        assert result["levelClass"] == "is-medium"

    def test_8_chars_only_specials_is_medium(self):
        # Length >= 8 AND has special, no number: 2 checks → medium
        result = _evaluate_password_strength("!@#$%^&*")
        assert result["levelClass"] == "is-medium"

    def test_space_counts_as_special_character(self):
        # Space is not [A-Za-z0-9], so it counts as a special character
        result = _evaluate_password_strength("password 1")
        # length >= 8, has number, has special (space): all 3 → strong
        assert result["levelClass"] == "is-strong"

    def test_unicode_special_counts_as_special_character(self):
        # Unicode char not in [A-Za-z0-9] counts as special
        result = _evaluate_password_strength("password1ñ")
        # length >= 8, has number, has special: all 3 → strong
        assert result["levelClass"] == "is-strong"

    def test_uppercase_only_long_is_weak(self):
        # Uppercase letters are [A-Za-z0-9], no special, no number: 1 check (length) → weak
        result = _evaluate_password_strength("ABCDEFGH")
        assert result["levelClass"] == "is-weak"

    def test_very_long_password_with_all_criteria_is_strong(self):
        result = _evaluate_password_strength("a" * 50 + "1!")
        assert result["levelClass"] == "is-strong"

    def test_result_always_returns_level_class_key(self):
        for pwd in ["", "a", "abcdefgh", "password1", "Password1!"]:
            result = _evaluate_password_strength(pwd)
            assert "levelClass" in result

    def test_result_always_returns_label_key(self):
        for pwd in ["", "a", "abcdefgh", "password1", "Password1!"]:
            result = _evaluate_password_strength(pwd)
            assert "label" in result

    def test_non_empty_weak_never_returns_empty_level_class(self):
        result = _evaluate_password_strength("a")
        assert result["levelClass"] != ""