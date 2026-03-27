import os
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_app():
    """Import a fresh app instance with current env vars applied."""
    import importlib
    import app.main as main_module

    importlib.reload(main_module)
    return main_module.app


class TestCorsConfiguration:
    """CORS origins should be configurable via CORS_ORIGINS env var."""

    def test_default_cors_allows_localhost_5173(self):
        """Without CORS_ORIGINS set, http://localhost:5173 is allowed."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CORS_ORIGINS", None)
            app = _make_app()
            client = TestClient(app)

        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_origins_env_var_overrides_default(self):
        """CORS_ORIGINS env var should configure allowed origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com,https://other.com"}):
            app = _make_app()
            client = TestClient(app)

        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "https://example.com"

    def test_cors_rejects_unlisted_origin(self):
        """An origin not in CORS_ORIGINS should not get CORS headers."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://allowed.com"}):
            app = _make_app()
            client = TestClient(app)

        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "https://evil.com"


class TestStaticFileServing:
    """Static files should be served when STATIC_DIR env var is set."""

    def test_no_static_mount_when_env_not_set(self):
        """Without STATIC_DIR, no static file route should exist."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STATIC_DIR", None)
            app = _make_app()
            client = TestClient(app)

        response = client.get("/index.html")
        assert response.status_code == 404

    def test_serves_static_files_when_static_dir_set(self):
        """When STATIC_DIR points to a directory, files are served."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "index.html")
            with open(index_path, "w") as f:
                f.write("<html><body>Hello</body></html>")

            with patch.dict(os.environ, {"STATIC_DIR": tmpdir}):
                app = _make_app()
                client = TestClient(app)
                response = client.get("/index.html")

            assert response.status_code == 200
            assert "Hello" in response.text

    def test_api_routes_still_work_with_static_dir_set(self):
        """API routes should take priority over static file serving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"STATIC_DIR": tmpdir}):
                app = _make_app()
                client = TestClient(app)
                response = client.get("/api/health")

            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_static_serves_index_html_as_fallback_for_spa(self):
        """Non-API, non-file paths should fall back to index.html for SPA routing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "index.html")
            with open(index_path, "w") as f:
                f.write("<html><body>SPA</body></html>")

            with patch.dict(os.environ, {"STATIC_DIR": tmpdir}):
                app = _make_app()
                client = TestClient(app)
                response = client.get("/some/spa/route")

            assert response.status_code == 200
            assert "SPA" in response.text
