"""Tests for Docker infrastructure files.

Verifies that Dockerfile, docker-compose.yml, docker-entrypoint.sh,
.dockerignore, and .env.example exist with correct structure and content.
"""

import os
import stat
from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).parent.parent.parent


class TestDockerfileExists:
    def test_dockerfile_exists_at_project_root(self):
        assert (ROOT_DIR / "Dockerfile").is_file()


class TestDockerfileMultiStage:
    @pytest.fixture
    def dockerfile_content(self):
        return (ROOT_DIR / "Dockerfile").read_text()

    def test_has_frontend_build_stage(self, dockerfile_content):
        assert "AS frontend-build" in dockerfile_content or "as frontend-build" in dockerfile_content

    def test_has_final_stage_based_on_python(self, dockerfile_content):
        # The final stage should use a Python base image
        lines = dockerfile_content.strip().splitlines()
        from_lines = [ln for ln in lines if ln.strip().upper().startswith("FROM")]
        assert len(from_lines) >= 2, "Multi-stage build requires at least 2 FROM instructions"
        # Last FROM should be Python-based
        last_from = from_lines[-1].lower()
        assert "python" in last_from

    def test_frontend_stage_uses_node(self, dockerfile_content):
        lines = dockerfile_content.strip().splitlines()
        from_lines = [ln for ln in lines if ln.strip().upper().startswith("FROM")]
        first_from = from_lines[0].lower()
        assert "node" in first_from

    def test_copies_frontend_build_output(self, dockerfile_content):
        # Should copy built frontend from the frontend-build stage
        assert "--from=frontend-build" in dockerfile_content or "--from=frontend" in dockerfile_content

    def test_installs_backend_dependencies(self, dockerfile_content):
        assert "pip install" in dockerfile_content or "uv" in dockerfile_content

    def test_copies_entrypoint_script(self, dockerfile_content):
        assert "docker-entrypoint.sh" in dockerfile_content

    def test_exposes_port_8000(self, dockerfile_content):
        assert "EXPOSE 8000" in dockerfile_content or "EXPOSE  8000" in dockerfile_content

    def test_sets_entrypoint_or_cmd(self, dockerfile_content):
        upper = dockerfile_content.upper()
        assert "ENTRYPOINT" in upper or "CMD" in upper


class TestDockerComposeExists:
    def test_docker_compose_file_exists(self):
        assert (ROOT_DIR / "docker-compose.yml").is_file()


class TestDockerComposeStructure:
    @pytest.fixture
    def compose_config(self):
        return yaml.safe_load((ROOT_DIR / "docker-compose.yml").read_text())

    def test_defines_app_service(self, compose_config):
        assert "services" in compose_config
        services = compose_config["services"]
        # Should have at least one service (the app)
        assert len(services) >= 1

    def test_app_service_builds_from_dockerfile(self, compose_config):
        services = compose_config["services"]
        app_service = next(iter(services.values()))
        build = app_service.get("build", {})
        # build can be a string "." or a dict with context
        if isinstance(build, str):
            assert build == "."
        else:
            assert build.get("context") in (".", None) or "dockerfile" in str(build).lower()

    def test_app_service_maps_port_8000(self, compose_config):
        services = compose_config["services"]
        app_service = next(iter(services.values()))
        ports = app_service.get("ports", [])
        port_strs = [str(p) for p in ports]
        assert any("8000" in p for p in port_strs), "Should map port 8000"

    def test_app_service_has_volume_for_database(self, compose_config):
        services = compose_config["services"]
        app_service = next(iter(services.values()))
        volumes = app_service.get("volumes", [])
        volume_strs = [str(v) for v in volumes]
        assert any("db" in v.lower() or "data" in v.lower() or "runway" in v.lower() for v in volume_strs), \
            "Should mount a volume for persistent database storage"

    def test_app_service_has_env_file_or_environment(self, compose_config):
        services = compose_config["services"]
        app_service = next(iter(services.values()))
        has_env = "environment" in app_service or "env_file" in app_service
        assert has_env, "Should configure environment variables"


class TestDockerEntrypointExists:
    def test_entrypoint_script_exists(self):
        assert (ROOT_DIR / "docker-entrypoint.sh").is_file()


class TestDockerEntrypointContent:
    @pytest.fixture
    def entrypoint_content(self):
        return (ROOT_DIR / "docker-entrypoint.sh").read_text()

    def test_has_shebang(self, entrypoint_content):
        assert entrypoint_content.startswith("#!/")

    def test_runs_alembic_migrations(self, entrypoint_content):
        assert "alembic upgrade head" in entrypoint_content

    def test_starts_uvicorn(self, entrypoint_content):
        assert "uvicorn" in entrypoint_content

    def test_is_executable(self):
        entrypoint = ROOT_DIR / "docker-entrypoint.sh"
        file_stat = os.stat(entrypoint)
        assert file_stat.st_mode & stat.S_IXUSR, "docker-entrypoint.sh should be executable"


class TestDockerignoreExists:
    def test_dockerignore_exists(self):
        assert (ROOT_DIR / ".dockerignore").is_file()


class TestDockerignoreContent:
    @pytest.fixture
    def dockerignore_entries(self):
        content = (ROOT_DIR / ".dockerignore").read_text()
        return [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    def test_ignores_git(self, dockerignore_entries):
        assert any(".git" in e for e in dockerignore_entries)

    def test_ignores_node_modules(self, dockerignore_entries):
        assert any("node_modules" in e for e in dockerignore_entries)

    def test_ignores_pycache(self, dockerignore_entries):
        assert any("__pycache__" in e for e in dockerignore_entries)

    def test_ignores_database_file(self, dockerignore_entries):
        assert any(".db" in e or "runway.db" in e for e in dockerignore_entries)


class TestEnvExampleExists:
    def test_env_example_exists(self):
        assert (ROOT_DIR / ".env.example").is_file()


class TestEnvExampleContent:
    @pytest.fixture
    def env_example_content(self):
        return (ROOT_DIR / ".env.example").read_text()

    def test_documents_database_path(self, env_example_content):
        assert "DATABASE_PATH" in env_example_content

    def test_documents_cors_origins(self, env_example_content):
        assert "CORS_ORIGINS" in env_example_content

    def test_documents_static_dir(self, env_example_content):
        assert "STATIC_DIR" in env_example_content
