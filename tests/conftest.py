"""Shared pytest fixtures for isolated application tests."""

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    """Create an app whose SQLite database lives only for this test."""
    database_path = tmp_path / "test-taskflow.sqlite"
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database_path),
        }
    )


@pytest.fixture()
def client(app):
    """Provide a Flask test client."""
    return app.test_client()
