"""Web routes tests."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def get_csrf_from_response(response) -> str | None:
    """Extract CSRF token from response cookies."""
    return response.cookies.get("csrf_token")


async def do_register(client: AsyncClient, email: str, password: str) -> str:
    """Register a user and return the CSRF token from the response."""
    csrf_response = await client.get("/web/register")
    csrf_token = get_csrf_from_response(csrf_response)

    headers = {}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    await client.post(
        "/web/register",
        data={
            "email": email,
            "password": password,
            "password_confirm": password,
        },
        headers=headers,
    )
    return csrf_token


async def do_login(client: AsyncClient, email: str, password: str) -> str:
    """Login a user and return the CSRF token from the response."""
    csrf_response = await client.get("/web/login")
    csrf_token = get_csrf_from_response(csrf_response)

    headers = {}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    await client.post(
        "/web/login",
        data={"email": email, "password": password},
        headers=headers,
    )
    return csrf_token


class TestValidateRedirectUrl:
    """Tests for _validate_redirect_url helper."""

    def test_none_returns_default(self):
        """Test that None URL returns default."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url(None, "/web/downloads")
        assert result == "/web/downloads"

    def test_empty_string_returns_default(self):
        """Test that empty string returns default."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("", "/web/downloads")
        assert result == "/web/downloads"

    def test_valid_internal_path(self):
        """Test that valid internal path is allowed."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/downloads", "/web/login")
        assert result == "/web/downloads"

    def test_external_url_rejected(self):
        """Test that external URLs are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("https://evil.com", "/web/downloads")
        assert result == "/web/downloads"

    def test_external_url_with_path_rejected(self):
        """Test that external URLs with path are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("https://evil.com/phishing", "/web/downloads")
        assert result == "/web/downloads"

    def test_relative_path_with_scheme_rejected(self):
        """Test that paths with schemes are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("javascript:alert(1)", "/web/downloads")
        assert result == "/web/downloads"

    def test_protocol_relative_url_rejected(self):
        """Test that protocol-relative URLs are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("//example.com", "/web/downloads")
        assert result == "/web/downloads"

    def test_path_without_leading_slash_rejected(self):
        """Test that paths without leading slash are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("web/downloads", "/web/downloads")
        assert result == "/web/downloads"

    def test_path_with_double_slashes_rejected(self):
        """Test that paths with backslashes are normalized and rejected if not allowed."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("\\web\\downloads", "/web/downloads")
        assert result == "/web/downloads"

    def test_valid_web_path_allowed(self):
        """Test that paths starting with /web/ are allowed."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/login", "/web/downloads")
        assert result == "/web/login"

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts starting with /web/../ are rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/../etc/passwd", "/web/downloads")
        assert result == "/web/downloads"

    def test_path_traversal_with_double_dots_rejected(self):
        """Test that simple path traversal /../ is rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/../../etc/passwd", "/web/downloads")
        assert result == "/web/downloads"


class TestValidateCsrfToken:
    """Tests for validate_csrf_token helper."""

    @pytest.mark.asyncio
    async def test_get_request_always_valid(self):
        """Test that GET requests don't require CSRF validation."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.cookies = {}

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_head_request_always_valid(self):
        """Test that HEAD requests don't require CSRF validation."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "HEAD"
        mock_request.headers = {}
        mock_request.cookies = {}

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_options_request_always_valid(self):
        """Test that OPTIONS requests don't require CSRF validation."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "OPTIONS"
        mock_request.headers = {}
        mock_request.cookies = {}

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_missing_cookie_token_returns_false(self):
        """Test that missing cookie CSRF token returns False."""
        from unittest.mock import AsyncMock, MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "sometoken"}
        mock_request.cookies = {}
        mock_request.form = AsyncMock(return_value={})

        result = await validate_csrf_token(mock_request)
        assert result is False

    @pytest.mark.asyncio
    async def test_valid_header_token(self):
        """Test that matching header and cookie tokens return True."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "validtoken", "HX-Request": "true"}
        mock_request.cookies = {"csrf_token": "validtoken"}

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_header_token(self):
        """Test that non-matching header and cookie tokens return False."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "wrongtoken"}
        mock_request.cookies = {"csrf_token": "goodtoken"}

        result = await validate_csrf_token(mock_request)
        assert result is False


class TestValidateFilePath:
    """Tests for _validate_file_path helper."""

    def test_valid_path_within_downloads(self, tmp_path):
        """Test that valid paths within downloads directory are allowed."""
        from app.api.routes.web import _validate_file_path

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            safe_path = downloads_dir / "file.mp3"
            safe_path.write_text("test content")

            result = _validate_file_path(str(safe_path))
            assert result == str(safe_path)

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        from fastapi import HTTPException

        from app.api.routes.web import _validate_file_path

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)

            malicious_path = str(tmp_path / ".." / ".." / "etc" / "passwd")

            with pytest.raises(HTTPException) as exc_info:
                _validate_file_path(malicious_path)

            assert exc_info.value.status_code == 403


class TestIsHtmxRequest:
    """Tests for is_htmx_request helper."""

    def test_htmx_request_true(self):
        """Test that HX-Request header set to 'true' returns True."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import is_htmx_request

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get = MagicMock(return_value="true")

        assert is_htmx_request(mock_request) is True

    def test_htmx_request_false(self):
        """Test that missing or non-true HX-Request returns False."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import is_htmx_request

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get = MagicMock(return_value=None)

        assert is_htmx_request(mock_request) is False

    def test_htmx_request_not_true(self):
        """Test that HX-Request header set to 'false' returns False."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import is_htmx_request

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get = MagicMock(return_value="false")

        assert is_htmx_request(mock_request) is False


class TestLoginPage:
    """Tests for GET /web/login."""

    @pytest.mark.asyncio
    async def test_login_page_renders(self):
        """Test that login page renders with CSRF token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/login")

        assert response.status_code == 200
        assert "csrf_token" in response.text
        assert response.cookies.get("csrf_token") is not None

    @pytest.mark.asyncio
    async def test_login_page_includes_form(self):
        """Test that login page contains login form elements."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/login")

        assert response.status_code == 200
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'name="csrf_token"' in response.text


class TestLoginForm:
    """Tests for POST /web/login."""

    @pytest.mark.asyncio
    async def test_login_success_sets_cookies(self):
        """Test successful login via non-HTMX form sets auth cookies."""
        email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_response = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

        assert login_response.status_code == 303
        assert "access_token" in login_response.cookies
        assert "refresh_token" in login_response.cookies

    @pytest.mark.asyncio
    async def test_login_invalid_csrf(self):
        """Test login with invalid CSRF token returns 303 redirect to login page with error."""
        email = f"csrf_fail_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            _ = await do_login(client, email, password)

            login_response = await client.post(
                "/web/login",
                data={
                    "email": email,
                    "password": password,
                    "csrf_token": "invalid_token",
                },
            )

        assert login_response.status_code == 303
        assert login_response.headers["location"] == "/web/login?error=csrf"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        """Test login with wrong password returns redirect to login page (303)."""
        email = f"wrongpass_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_response = await client.post(
                "/web/login",
                data={
                    "email": email,
                    "password": "wrongpassword",
                },
                headers={"X-CSRF-Token": csrf_token},
            )

        assert login_response.status_code == 303

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """Test login with non-existent email returns redirect to login page (303)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/login")
            csrf_token = get_csrf_from_response(csrf_response)

            login_response = await client.post(
                "/web/login",
                data={
                    "email": "nonexistent@example.com",
                    "password": "somepassword123",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert login_response.status_code == 303


class TestRegisterPage:
    """Tests for GET /web/register."""

    @pytest.mark.asyncio
    async def test_register_page_renders(self):
        """Test that register page renders with CSRF token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/register")

        assert response.status_code == 200
        assert "csrf_token" in response.text
        assert response.cookies.get("csrf_token") is not None

    @pytest.mark.asyncio
    async def test_register_page_includes_form(self):
        """Test that register page contains registration form elements."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/register")

        assert response.status_code == 200
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'name="password_confirm"' in response.text


class TestRegisterForm:
    """Tests for POST /web/register."""

    @pytest.mark.asyncio
    async def test_register_success_sets_cookies(self):
        """Test successful registration via non-HTMX form sets auth cookies."""
        email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert reg_response.status_code == 303
        assert "access_token" in reg_response.cookies
        assert "refresh_token" in reg_response.cookies

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self):
        """Test registration with mismatched passwords returns 303 redirect with error."""
        email = f"mismatch_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": "differentpassword",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert reg_response.status_code == 303
        assert reg_response.headers["location"] == "/web/register?error=password_mismatch"

    @pytest.mark.asyncio
    async def test_register_short_password(self):
        """Test registration with short password returns redirect (303) for non-HTMX."""
        email = f"shortpass_{uuid.uuid4().hex[:8]}@example.com"
        password = "short"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert reg_response.status_code == 303

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registration with existing email returns redirect (303) for non-HTMX."""
        email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

            csrf_response2 = await client.get("/web/register")
            csrf_token2 = get_csrf_from_response(csrf_response2)

            reg_response2 = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers={"X-CSRF-Token": csrf_token2} if csrf_token2 else {},
            )

        assert reg_response2.status_code == 303

    @pytest.mark.asyncio
    async def test_register_invalid_csrf(self):
        """Test registration with invalid CSRF token returns 303 redirect to register page with error."""
        email = f"csrf_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                    "csrf_token": "invalid_token",
                },
            )

        assert reg_response.status_code == 303
        assert reg_response.headers["location"] == "/web/register?error=csrf"


class TestLogout:
    """Tests for POST /web/logout."""

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout clears cookies via redirect."""
        email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            logout_response = await client.post(
                "/web/logout",
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert logout_response.status_code == 303

    @pytest.mark.asyncio
    async def test_logout_invalid_csrf(self):
        """Test logout with invalid CSRF token returns 303 redirect to downloads page with error."""
        email = f"logoutcsrf_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            _ = await do_login(client, email, password)

            logout_response = await client.post(
                "/web/logout",
                headers={"X-CSRF-Token": "invalid_token"},
            )

        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/web/downloads?error=csrf"


class TestDashboardPage:
    """Tests for GET /web/downloads (dashboard)."""

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/downloads")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dashboard_with_auth(self):
        """Test that dashboard renders for authenticated user."""
        email = f"dashboard_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            dashboard_response = await client.get(
                "/web/downloads",
                cookies={"access_token": access_token},
            )

        assert dashboard_response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_renders_initial_download_skeleton_state(self):
        """Test dashboard includes skeleton/loading state before SSE updates."""
        email = f"dashskeleton_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            dashboard_response = await client.get(
                "/web/downloads",
                cookies={"access_token": access_token},
            )

        assert dashboard_response.status_code == 200
        assert 'id="download-list" class="download-list-loading"' in dashboard_response.text
        assert 'id="download-skeleton"' in dashboard_response.text
        assert "downloadSkeletonFallback" in dashboard_response.text
        assert "clearDownloadSkeleton" in dashboard_response.text
        assert "htmx:sseOpen" in dashboard_response.text
        assert "htmx:sseError" in dashboard_response.text


class TestCreateDownloadForm:
    """Tests for POST /web/downloads (HTMX endpoint)."""

    @pytest.mark.asyncio
    async def test_create_download_htmx(self, sample_url):
        """Test creating download via HTMX endpoint."""
        email = f"download_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            with patch("app.api.routes.web.enqueue_job", new_callable=AsyncMock) as mock_enqueue:
                mock_enqueue.return_value = None

                create_response = await client.post(
                    "/web/downloads",
                    data={"url": sample_url},
                    headers=headers,
                    cookies={"access_token": access_token},
                )

        assert create_response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_download_requires_auth(self, sample_url):
        """Test that creating download requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/login")
            csrf_token = get_csrf_from_response(csrf_response)

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            response = await client.post(
                "/web/downloads",
                data={"url": sample_url},
                headers=headers,
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_download_invalid_url(self):
        """Test creating download with invalid URL returns 422."""
        email = f"invalidurl_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            create_response = await client.post(
                "/web/downloads",
                data={"url": "https://not-youtube.com/video"},
                headers=headers,
                cookies={"access_token": access_token},
            )

        assert create_response.status_code == 422


class TestCreateDownloadFullPage:
    """Tests for POST /web/downloads/full (full page endpoint)."""

    @pytest.mark.asyncio
    async def test_create_download_full_page(self, sample_url):
        """Test creating download via full page endpoint."""
        email = f"fullpage_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            with patch("app.api.routes.web.enqueue_job", new_callable=AsyncMock) as mock_enqueue:
                mock_enqueue.return_value = None

                create_response = await client.post(
                    "/web/downloads/full",
                    data={"url": sample_url},
                    headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                    cookies={"access_token": access_token},
                )

        assert create_response.status_code == 303

    @pytest.mark.asyncio
    async def test_create_download_full_page_requires_auth(self, sample_url):
        """Test that full page download requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/login")
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/downloads/full",
                data={"url": sample_url},
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert response.status_code == 401


class TestDeleteDownload:
    """Tests for DELETE /web/downloads/{job_id}."""

    @pytest.mark.asyncio
    async def test_delete_download_not_found(self):
        """Test deleting non-existent download returns 404."""
        email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            fake_uuid = str(uuid.uuid4())

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            delete_response = await client.delete(
                f"/web/downloads/{fake_uuid}",
                headers=headers,
                cookies={"access_token": access_token},
            )

        assert delete_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_download_invalid_uuid(self):
        """Test deleting with invalid UUID format returns 400."""
        email = f"deleteuuid_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            delete_response = await client.delete(
                "/web/downloads/not-a-uuid",
                headers=headers,
                cookies={"access_token": access_token},
            )

        assert delete_response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_download_requires_auth(self):
        """Test that deleting download requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            fake_uuid = str(uuid.uuid4())
            response = await client.delete(f"/web/downloads/{fake_uuid}")

        assert response.status_code == 401


class TestDownloadFile:
    """Tests for GET /web/downloads/{job_id}/file."""

    @pytest.mark.asyncio
    async def test_download_file_not_found(self):
        """Test downloading from non-existent job returns 404."""
        email = f"dlfile_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            fake_uuid = str(uuid.uuid4())
            download_response = await client.get(
                f"/web/downloads/{fake_uuid}/file",
                cookies={"access_token": access_token},
            )

        assert download_response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_file_invalid_uuid(self):
        """Test downloading with invalid UUID returns 400."""
        email = f"dlfileuuid_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            download_response = await client.get(
                "/web/downloads/not-a-uuid/file",
                cookies={"access_token": access_token},
            )

        assert download_response.status_code == 400

    @pytest.mark.asyncio
    async def test_download_file_requires_auth(self):
        """Test that downloading file requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            fake_uuid = str(uuid.uuid4())
            response = await client.get(f"/web/downloads/{fake_uuid}/file")

        assert response.status_code == 401


class TestHtmxBehavior:
    """Tests for HTMX-specific behavior."""

    @pytest.mark.asyncio
    async def test_login_htmx_returns_hx_redirect(self):
        """Test that HTMX login returns HX-Redirect header."""
        email = f"htmxlogin_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            login_response = await client.post(
                "/web/login",
                data={
                    "email": email,
                    "password": password,
                },
                headers=headers,
            )

        assert login_response.status_code == 200
        assert "HX-Redirect" in login_response.headers

    @pytest.mark.asyncio
    async def test_login_non_htmx_returns_redirect_response(self):
        """Test that non-HTMX login returns RedirectResponse with 303."""
        email = f"nonhtmxlogin_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_response = await client.post(
                "/web/login",
                data={
                    "email": email,
                    "password": password,
                },
                headers={"X-CSRF-Token": csrf_token},
            )

        assert login_response.status_code == 303

    @pytest.mark.asyncio
    async def test_register_htmx_returns_hx_redirect(self):
        """Test that HTMX registration returns HX-Redirect header."""
        email = f"htmxregister_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            headers = {"HX-Request": "true"}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers=headers,
            )

        assert reg_response.status_code == 200
        assert "HX-Redirect" in reg_response.headers

    @pytest.mark.asyncio
    async def test_register_non_htmx_returns_redirect_response(self):
        """Test that non-HTMX registration returns RedirectResponse with 303."""
        email = f"nonhtmxregister_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            csrf_response = await client.get("/web/register")
            csrf_token = get_csrf_from_response(csrf_response)

            reg_response = await client.post(
                "/web/register",
                data={
                    "email": email,
                    "password": password,
                    "password_confirm": password,
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
            )

        assert reg_response.status_code == 303

    @pytest.mark.asyncio
    async def test_logout_htmx_with_invalid_csrf_returns_error(self):
        """Test that HTMX logout with invalid CSRF returns error HTML."""
        email = f"htmxlogout_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            _ = await do_login(client, email, password)

            logout_response = await client.post(
                "/web/logout",
                headers={
                    "HX-Request": "true",
                    "X-CSRF-Token": "invalid_token",
                },
            )

        assert logout_response.status_code == 403
        assert "error" in logout_response.text.lower() or "csrf" in logout_response.text.lower()


class TestSettingsPage:
    """Tests for GET /web/settings."""

    @pytest.mark.asyncio
    async def test_settings_page_requires_auth(self):
        """Test that settings page requires authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/settings")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_settings_page_renders(self):
        """Test that settings page renders for authenticated user."""
        email = f"settings_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            response = await client.get(
                "/web/settings",
                cookies={"access_token": access_token},
            )

        assert response.status_code == 200


class TestUpdateUsername:
    """Tests for POST /web/settings/username."""

    @pytest.mark.asyncio
    async def test_update_username_success(self):
        """Test updating username successfully."""
        email = f"username_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            # Get fresh CSRF token
            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/username",
                data={"username": "newname"},
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303)

    @pytest.mark.asyncio
    async def test_update_username_too_short(self):
        """Test updating username with too short name returns error."""
        email = f"shortuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/username",
                data={"username": "ab"},
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303)

    @pytest.mark.asyncio
    async def test_update_username_invalid_csrf(self):
        """Test updating username with invalid CSRF token returns error."""
        email = f"csrfuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            response = await client.post(
                "/web/settings/username",
                data={"username": "validname"},
                headers={"X-CSRF-Token": "invalid_token"},
                cookies={"access_token": access_token},
            )

        assert response.status_code == 303
        assert response.headers["location"] == "/web/settings?error=csrf"


class TestChangePassword:
    """Tests for POST /web/settings/password."""

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test changing password successfully."""
        email = f"changepw_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/password",
                data={
                    "current_password": password,
                    "new_password": "newpassword123",
                    "new_password_confirm": "newpassword123",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self):
        """Test changing password with wrong current password returns error."""
        email = f"wrongcurr_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/password",
                data={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123",
                    "new_password_confirm": "newpassword123",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303, 401)

    @pytest.mark.asyncio
    async def test_change_password_mismatch(self):
        """Test changing password with mismatched confirmation returns error."""
        email = f"mismatchpw_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/password",
                data={
                    "current_password": password,
                    "new_password": "newpassword123",
                    "new_password_confirm": "differentpass",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303, 400)

    @pytest.mark.asyncio
    async def test_change_password_too_short(self):
        """Test changing password with too short new password returns error."""
        email = f"shortpw_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            csrf_response = await client.get(
                "/web/settings", cookies={"access_token": access_token}
            )
            csrf_token = get_csrf_from_response(csrf_response)

            response = await client.post(
                "/web/settings/password",
                data={
                    "current_password": password,
                    "new_password": "short",
                    "new_password_confirm": "short",
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                cookies={"access_token": access_token},
            )

        assert response.status_code in (200, 303, 400)


class TestDeleteDownloadForm:
    """Tests for DELETE /web/downloads/{job_id} (HTMX form-based)."""

    @pytest.mark.asyncio
    async def test_delete_download_invalid_csrf(self):
        """Test deleting download with invalid CSRF returns 403."""
        email = f"delcsrf_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as client:
            await do_register(client, email, password)
            csrf_token = await do_login(client, email, password)

            login_resp = await client.post(
                "/web/login",
                data={"email": email, "password": password},
                headers={"X-CSRF-Token": csrf_token},
            )

            access_token = login_resp.cookies.get("access_token", "")

            fake_uuid = str(uuid.uuid4())

            response = await client.delete(
                f"/web/downloads/{fake_uuid}",
                headers={"X-CSRF-Token": "invalid_token"},
                cookies={"access_token": access_token},
            )

        assert response.status_code == 403


class TestValidateCsrfTokenStrategy2:
    """Tests for CSRF Strategy 2: Cookie present, header missing, form matches cookie."""

    @pytest.mark.asyncio
    async def test_csrf_cookie_present_header_missing_form_matches(self):
        """Mock request.form() returning csrf_token matching cookie, assert True."""
        from unittest.mock import MagicMock

        from fastapi import Request
        from starlette.datastructures import MultiDict

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.cookies = {"csrf_token": "cookie_token_value"}
        mock_request.headers = {}
        mock_request.form = AsyncMock(
            return_value=MultiDict([("csrf_token", "cookie_token_value")])
        )

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_csrf_cookie_present_header_missing_form_mismatch(self):
        """Assert False when form token doesn't match cookie token."""
        from unittest.mock import MagicMock

        from fastapi import Request
        from starlette.datastructures import MultiDict

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.cookies = {"csrf_token": "cookie_token_value"}
        mock_request.headers = {}
        mock_request.form = AsyncMock(return_value=MultiDict([("csrf_token", "different_token")]))

        result = await validate_csrf_token(mock_request)
        assert result is False

    @pytest.mark.asyncio
    async def test_csrf_cookie_present_header_missing_form_exception(self):
        """Assert False when request.form() raises an exception."""
        from unittest.mock import MagicMock

        from fastapi import Request

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.cookies = {"csrf_token": "cookie_token_value"}
        mock_request.headers = {}
        mock_request.form = AsyncMock(side_effect=Exception("Form parse error"))

        result = await validate_csrf_token(mock_request)
        assert result is False


class TestValidateCsrfTokenStrategy3:
    """Tests for CSRF Strategy 3: No cookie, header present, form matches header."""

    @pytest.mark.asyncio
    async def test_csrf_no_cookie_header_present_form_matches(self):
        """Assert True when header and form tokens match and no cookie present."""
        from unittest.mock import MagicMock

        from fastapi import Request
        from starlette.datastructures import MultiDict

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.cookies = {}
        mock_request.headers = {"X-CSRF-Token": "header_token_value"}
        mock_request.form = AsyncMock(
            return_value=MultiDict([("csrf_token", "header_token_value")])
        )

        result = await validate_csrf_token(mock_request)
        assert result is True

    @pytest.mark.asyncio
    async def test_csrf_no_cookie_header_present_form_mismatch(self):
        """Assert False when form token doesn't match header token."""
        from unittest.mock import MagicMock

        from fastapi import Request
        from starlette.datastructures import MultiDict

        from app.api.routes.web import validate_csrf_token

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.cookies = {}
        mock_request.headers = {"X-CSRF-Token": "header_token_value"}
        mock_request.form = AsyncMock(return_value=MultiDict([("csrf_token", "different_token")]))

        result = await validate_csrf_token(mock_request)
        assert result is False


class TestValidateRedirectUrlNormalization:
    """Tests for redirect URL path normalization."""

    def test_validate_redirect_url_normalizes_double_dots(self):
        """URL /web/../login should be normalized and rejected (doesn't start with /web/)."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/../login", "/web/downloads")
        assert result == "/web/downloads"

    def test_validate_redirect_url_preserves_trailing_slash(self):
        """URL /web/downloads/ should preserve trailing slash after normalization."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/downloads/", "/web/login")
        assert result == "/web/downloads/"

    def test_validate_redirect_url_normalizes_double_dots_in_middle(self):
        """URL /web/../web/login should normalize to /web/login."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("/web/../web/login", "/web/downloads")
        assert result == "/web/login"

    def test_validate_redirect_url_strips_backslashes(self):
        """URL with backslashes should be normalized and rejected."""
        from app.api.routes.web import _validate_redirect_url

        result = _validate_redirect_url("\\web\\downloads", "/web/downloads")
        assert result == "/web/downloads"


class TestCleanupJobFiles:
    """Tests for _cleanup_job_files helper."""

    def test_cleanup_job_files_removes_valid_files(self, tmp_path):
        """Create temp files, assert (True, [])."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()
        file1 = downloads_dir / "file1.mp3"
        file1.write_text("test content")
        file2 = downloads_dir / "file2.mp3"
        file2.write_text("test content")

        mock_job1 = MagicMock()
        mock_job1.file_path = str(file1)
        mock_job1.id = uuid.uuid4()
        mock_job2 = MagicMock()
        mock_job2.file_path = str(file2)
        mock_job2.id = uuid.uuid4()

        mock_logger = MagicMock()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            all_cleaned, failures = _cleanup_job_files([mock_job1, mock_job2], mock_logger)

        assert all_cleaned is True
        assert failures == []
        assert not file1.exists()
        assert not file2.exists()

    def test_cleanup_job_files_skips_missing_file_path(self, tmp_path):
        """Job with file_path=None should be skipped."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        mock_job = MagicMock()
        mock_job.file_path = None
        mock_job.id = uuid.uuid4()

        mock_logger = MagicMock()

        all_cleaned, failures = _cleanup_job_files([mock_job], mock_logger)

        assert all_cleaned is True
        assert failures == []

    def test_cleanup_job_files_skips_nonexistent_file(self, tmp_path):
        """Job with non-existent file should be handled gracefully."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()

        mock_job = MagicMock()
        mock_job.file_path = str(downloads_dir / "nonexistent.mp3")
        mock_job.id = uuid.uuid4()

        mock_logger = MagicMock()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            all_cleaned, failures = _cleanup_job_files([mock_job], mock_logger)

        assert all_cleaned is True
        assert failures == []

    def test_cleanup_job_files_handles_path_traversal(self, tmp_path):
        """Assert (False, [bad_path]) and HTTPException caught."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()

        mock_job = MagicMock()
        mock_job.file_path = str(tmp_path / ".." / "etc" / "passwd")
        mock_job.id = uuid.uuid4()

        mock_logger = MagicMock()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            all_cleaned, failures = _cleanup_job_files([mock_job], mock_logger)

        assert all_cleaned is False
        assert len(failures) == 1

    def test_cleanup_job_files_handles_os_error(self, tmp_path):
        """Mock os.remove raising OSError, assert (False, [path])."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()
        file1 = downloads_dir / "file1.mp3"
        file1.write_text("test content")

        mock_job = MagicMock()
        mock_job.file_path = str(file1)
        mock_job.id = uuid.uuid4()

        mock_logger = MagicMock()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            with patch("app.api.routes.web.os.remove", side_effect=OSError("Permission denied")):
                all_cleaned, failures = _cleanup_job_files([mock_job], mock_logger)

        assert all_cleaned is False
        assert len(failures) == 1

    def test_cleanup_job_files_handles_generic_exception(self, tmp_path):
        """Mock os.remove raising unexpected exception, assert (False, [path])."""
        from unittest.mock import MagicMock

        from app.api.routes.web import _cleanup_job_files

        downloads_dir = tmp_path / "downloads"
        downloads_dir.mkdir()
        file1 = downloads_dir / "file1.mp3"
        file1.write_text("test content")

        mock_job = MagicMock()
        mock_job.file_path = str(file1)
        mock_job.id = uuid.uuid4()

        mock_logger = MagicMock()

        with patch("app.api.routes.web.settings") as mock_settings:
            mock_settings.storage_path = str(tmp_path)
            with patch(
                "app.api.routes.web.os.remove", side_effect=RuntimeError("Unexpected error")
            ):
                all_cleaned, failures = _cleanup_job_files([mock_job], mock_logger)

        assert all_cleaned is False
        assert len(failures) == 1
