"""Tests for Docker documentation in README.md.

Verifies that README.md contains Docker quickstart, existing DB migration,
AI/Ollama setup, and environment variable documentation.
"""

from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent.parent


@pytest.fixture
def readme_content():
    return (ROOT_DIR / "README.md").read_text()


@pytest.fixture
def readme_lower(readme_content):
    return readme_content.lower()


class TestDockerQuickstartSection:
    """README should document how to run Runway with Docker."""

    def test_has_docker_section_heading(self, readme_content):
        assert "## Docker" in readme_content or "## Running with Docker" in readme_content \
            or "# Docker" in readme_content

    def test_documents_docker_compose_up(self, readme_content):
        assert "docker compose up" in readme_content or "docker-compose up" in readme_content

    def test_documents_building_the_image(self, readme_lower):
        assert "docker compose build" in readme_lower or "docker build" in readme_lower

    def test_mentions_localhost_8000_in_docker_context(self, readme_content):
        # Docker section should mention accessing the app on localhost:8000
        # Find the Docker section and check port is mentioned there
        docker_idx = -1
        for heading in ["## Docker", "## Running with Docker"]:
            idx = readme_content.find(heading)
            if idx != -1:
                docker_idx = idx
                break
        assert docker_idx != -1, "Docker section heading not found"
        docker_section = readme_content[docker_idx:]
        assert "8000" in docker_section


class TestExistingDatabaseMigration:
    """README should explain how to use an existing database with Docker."""

    def test_documents_volume_mount_for_existing_db(self, readme_content):
        # Docker section should mention mounting or mapping database files
        docker_idx = -1
        for heading in ["## Docker", "## Running with Docker"]:
            idx = readme_content.find(heading)
            if idx != -1:
                docker_idx = idx
                break
        assert docker_idx != -1, "Docker section heading not found"
        docker_section = readme_content[docker_idx:].lower()
        assert "volume" in docker_section or "mount" in docker_section or "runway.db" in docker_section

    def test_documents_database_path_env_var(self, readme_content):
        assert "DATABASE_PATH" in readme_content


class TestAiOllamaDockerSetup:
    """README should explain Ollama/AI configuration with Docker."""

    def test_documents_ollama_in_docker_context(self, readme_content):
        # Docker section should mention Ollama configuration
        docker_idx = -1
        for heading in ["## Docker", "## Running with Docker"]:
            idx = readme_content.find(heading)
            if idx != -1:
                docker_idx = idx
                break
        assert docker_idx != -1, "Docker section heading not found"
        docker_section = readme_content[docker_idx:].lower()
        assert "ollama" in docker_section

    def test_documents_connecting_to_host_ollama(self, readme_content):
        # Should explain how to connect container to host Ollama instance
        docker_idx = -1
        for heading in ["## Docker", "## Running with Docker"]:
            idx = readme_content.find(heading)
            if idx != -1:
                docker_idx = idx
                break
        assert docker_idx != -1, "Docker section heading not found"
        docker_section = readme_content[docker_idx:].lower()
        assert "host.docker.internal" in docker_section or "network" in docker_section \
            or "ollama_base_url" in docker_section


class TestEnvironmentVariablesDocumentation:
    """README should document available environment variables."""

    def test_documents_env_file_or_env_example(self, readme_content):
        assert ".env" in readme_content

    def test_documents_cors_origins_var(self, readme_content):
        assert "CORS_ORIGINS" in readme_content

    def test_documents_database_path_var(self, readme_content):
        assert "DATABASE_PATH" in readme_content

    def test_references_env_example_file(self, readme_content):
        assert ".env.example" in readme_content or ".env" in readme_content
