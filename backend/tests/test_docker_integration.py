"""Integration tests for Docker container build and runtime.

These tests build the Docker image, start a container, and verify:
- Health check endpoint responds
- Frontend static files are served
- API endpoints work end-to-end
- Data persists across container restarts
- Alembic migrations run on existing databases

Requires Docker to be installed and running.
Mark all tests with @pytest.mark.docker so they can be skipped in CI
or when Docker is unavailable.
"""

import shutil
import socket
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest
import httpx

ROOT_DIR = Path(__file__).parent.parent.parent

# Skip entire module if Docker is not available
pytestmark = pytest.mark.docker

docker_available = shutil.which("docker") is not None


def _free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_healthy(url, timeout=60, interval=1):
    """Poll a URL until it returns 200 or timeout is reached."""
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=5)
            if resp.status_code == 200:
                return resp
        except (httpx.ConnectError, httpx.ReadError, httpx.TimeoutException) as e:
            last_error = e
        time.sleep(interval)
    raise TimeoutError(
        f"Container did not become healthy at {url} within {timeout}s. Last error: {last_error}"
    )


IMAGE_NAME = "runway-integration-test"


@pytest.fixture(scope="module")
def docker_image():
    """Build the Docker image once for all tests in this module."""
    if not docker_available:
        pytest.skip("Docker is not installed or not in PATH")

    result = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, "."],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        pytest.fail(f"Docker build failed:\n{result.stderr}")

    yield IMAGE_NAME

    # Cleanup image after tests
    subprocess.run(
        ["docker", "rmi", IMAGE_NAME],
        capture_output=True,
        timeout=30,
    )


@pytest.fixture
def container(docker_image, tmp_path):
    """Run a container and yield (container_id, base_url). Stops on teardown."""
    port = _free_port()
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    result = subprocess.run(
        [
            "docker", "run", "-d",
            "-p", f"{port}:8000",
            "-v", f"{data_dir}:/app/data",
            "-e", "DATABASE_PATH=/app/data/runway.db",
            "-e", "CORS_ORIGINS=*",
            "-e", "STATIC_DIR=/app/frontend/build",
            docker_image,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        pytest.fail(f"Docker run failed:\n{result.stderr}")

    container_id = result.stdout.strip()
    base_url = f"http://localhost:{port}"

    try:
        _wait_for_healthy(f"{base_url}/api/health")
    except TimeoutError:
        logs = subprocess.run(
            ["docker", "logs", container_id],
            capture_output=True, text=True, timeout=10,
        )
        subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, timeout=10)
        pytest.fail(f"Container failed to start. Logs:\n{logs.stdout}\n{logs.stderr}")

    yield container_id, base_url, data_dir

    subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, timeout=10)


class TestDockerBuild:
    def test_image_builds_successfully(self, docker_image):
        """The Docker image builds without errors."""
        result = subprocess.run(
            ["docker", "image", "inspect", docker_image],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, "Built image should be inspectable"


class TestHealthCheck:
    def test_health_endpoint_returns_ok(self, container):
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/api/health", timeout=5)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestFrontendServing:
    def test_root_returns_html(self, container):
        """The root URL serves the frontend index.html."""
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/", timeout=5)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_spa_fallback_returns_html_for_unknown_route(self, container):
        """Non-API routes fall back to index.html for SPA routing."""
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/some/frontend/route", timeout=5)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


class TestAPIEndpoints:
    def test_api_postings_returns_list(self, container):
        """The postings API returns a valid response."""
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/api/postings", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict)), "Postings endpoint should return JSON"

    def test_api_companies_returns_list(self, container):
        """The companies API returns a valid response."""
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/api/companies", timeout=5)
        assert resp.status_code == 200

    def test_api_dashboard_returns_data(self, container):
        """The dashboard API returns a valid response."""
        _, base_url, _ = container
        resp = httpx.get(f"{base_url}/api/dashboard", timeout=5)
        assert resp.status_code == 200


class TestDataPersistence:
    def test_database_created_in_mounted_volume(self, container):
        """The SQLite database file is created in the mounted data directory."""
        _, _, data_dir = container
        db_path = data_dir / "runway.db"
        assert db_path.is_file(), "Database should be created at DATABASE_PATH in the volume"

    def test_data_survives_container_restart(self, docker_image, tmp_path):
        """Data written in one container is available after restart."""
        port = _free_port()
        data_dir = tmp_path / "persist-data"
        data_dir.mkdir()

        # Start first container
        run1 = subprocess.run(
            [
                "docker", "run", "-d",
                "-p", f"{port}:8000",
                "-v", f"{data_dir}:/app/data",
                "-e", "DATABASE_PATH=/app/data/runway.db",
                "-e", "CORS_ORIGINS=*",
                "-e", "STATIC_DIR=/app/frontend/build",
                docker_image,
            ],
            capture_output=True, text=True, timeout=30,
        )
        cid1 = run1.stdout.strip()
        base_url = f"http://localhost:{port}"

        try:
            _wait_for_healthy(f"{base_url}/api/health")

            # Create a company via the API
            resp = httpx.post(
                f"{base_url}/api/companies",
                json={"name": "Persistence Test Corp"},
                timeout=5,
            )
            assert resp.status_code in (200, 201), f"Failed to create company: {resp.text}"
            resp.json().get("id")
        finally:
            subprocess.run(["docker", "rm", "-f", cid1], capture_output=True, timeout=10)

        # Start second container with same volume
        port2 = _free_port()
        run2 = subprocess.run(
            [
                "docker", "run", "-d",
                "-p", f"{port2}:8000",
                "-v", f"{data_dir}:/app/data",
                "-e", "DATABASE_PATH=/app/data/runway.db",
                "-e", "CORS_ORIGINS=*",
                "-e", "STATIC_DIR=/app/frontend/build",
                docker_image,
            ],
            capture_output=True, text=True, timeout=30,
        )
        cid2 = run2.stdout.strip()
        base_url2 = f"http://localhost:{port2}"

        try:
            _wait_for_healthy(f"{base_url2}/api/health")

            # Verify the company still exists
            resp = httpx.get(f"{base_url2}/api/companies", timeout=5)
            assert resp.status_code == 200
            companies = resp.json()
            names = [c["name"] for c in companies]
            assert "Persistence Test Corp" in names, "Data should persist across container restarts"
        finally:
            subprocess.run(["docker", "rm", "-f", cid2], capture_output=True, timeout=10)


class TestExistingDatabaseMigration:
    def test_container_starts_with_preexisting_database(self, docker_image, tmp_path):
        """Container runs Alembic migrations on a pre-existing database."""
        data_dir = tmp_path / "migration-data"
        data_dir.mkdir()
        db_path = data_dir / "runway.db"

        # Create a bare SQLite database (simulates an old DB that needs migration)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE IF NOT EXISTS _dummy (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        assert db_path.is_file(), "Pre-existing database should exist before container start"

        port = _free_port()
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "-p", f"{port}:8000",
                "-v", f"{data_dir}:/app/data",
                "-e", "DATABASE_PATH=/app/data/runway.db",
                "-e", "CORS_ORIGINS=*",
                "-e", "STATIC_DIR=/app/frontend/build",
                docker_image,
            ],
            capture_output=True, text=True, timeout=30,
        )
        cid = result.stdout.strip()
        base_url = f"http://localhost:{port}"

        try:
            _wait_for_healthy(f"{base_url}/api/health")

            # Verify the app is functional after migrating
            resp = httpx.get(f"{base_url}/api/health", timeout=5)
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

            # Verify Alembic version table was created (migration ran)
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            )
            tables = cursor.fetchall()
            conn.close()
            assert len(tables) == 1, "Alembic should have created the alembic_version table"
        finally:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=10)
