"""Tests for configurable database path via DATABASE_PATH env var."""

import importlib
import os

import pytest


class TestDatabasePathConfig:
    """Verify DATABASE_PATH env var controls the database location."""

    def test_defaults_to_runway_db_in_backend_dir(self):
        """When DATABASE_PATH is not set, DB_PATH should default to backend/runway.db."""
        env = os.environ.copy()
        env.pop("DATABASE_PATH", None)

        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("DATABASE_PATH", raising=False)
            import app.database

            importlib.reload(app.database)
            assert app.database.DB_PATH.name == "runway.db"
            assert str(app.database.DB_PATH).endswith("backend/runway.db")

    def test_uses_database_path_env_var_when_set(self, tmp_path):
        """When DATABASE_PATH is set, DB_PATH and DATABASE_URL should reflect it."""
        custom_path = str(tmp_path / "custom.db")

        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_PATH", custom_path)
            import app.database

            importlib.reload(app.database)
            assert str(app.database.DB_PATH) == custom_path
            assert app.database.DATABASE_URL == f"sqlite:///{custom_path}"

    def test_database_url_uses_configured_path(self, tmp_path):
        """DATABASE_URL should be derived from DB_PATH, not hardcoded."""
        custom_path = str(tmp_path / "other.db")

        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_PATH", custom_path)
            import app.database

            importlib.reload(app.database)
            assert custom_path in app.database.DATABASE_URL
