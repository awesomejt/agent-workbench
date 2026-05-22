"""
Pytest fixtures for Agent Workbench API tests.

Uses a dedicated `agent_workbench_test` database. Migrations run once per
session; each test gets a clean slate via TRUNCATE before it runs.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text

from agent_workbench.app import create_app
from agent_workbench.config import Settings
from agent_workbench.database import db as _db

_TEST_DATABASE_URL = os.environ.get(
    "AGENT_WORKBENCH_TEST_DATABASE_URL",
    "postgresql+psycopg://agent_workbench:agent_workbench_local@localhost:5433/agent_workbench_test",
)

_ALL_TABLES = (
    "agent_workbench.events, agent_workbench.reviews, agent_workbench.runs, "
    "agent_workbench.tasks, agent_workbench.project_statuses, "
    "agent_workbench.project_sections, agent_workbench.projects, agent_workbench.agents"
)


@pytest.fixture(scope="session")
def app() -> Iterator[Flask]:
    """Flask application pointed at the test database."""
    settings = Settings(
        app_env="local",
        database_url=_TEST_DATABASE_URL,
        secret_key="test-secret",
    )
    flask_app = create_app(settings)
    flask_app.config["TESTING"] = True

    with flask_app.app_context():
        _run_migrations()
        yield flask_app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app: Flask) -> Iterator[None]:  # noqa: ARG001
    """Truncate all tables before every test.

    Flask-SQLAlchemy 3.x scopes the session to the app context, not per-request.
    The outer app context (from the session-scoped `app` fixture) is already
    active here. Calling rollback()+remove() on *that* context's session releases
    any idle-in-transaction connection before TRUNCATE needs its exclusive lock.
    """
    _db.session.rollback()
    _db.session.remove()
    with _db.engine.connect() as conn:
        conn.execute(text(f"TRUNCATE {_ALL_TABLES} CASCADE"))
        conn.commit()
    yield


def _run_migrations() -> None:
    """Apply Alembic migrations to the test database (session-scoped)."""
    import os as _os

    from alembic import command
    from alembic.config import Config

    migrations_dir = _os.path.join(_os.path.dirname(__file__), "..", "migrations")
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", _os.path.abspath(migrations_dir))

    # env.py reads DATABASE_URL from the environment; set it temporarily
    saved = {k: _os.environ.get(k) for k in ("DATABASE_URL", "APP_ENV")}
    _os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
    _os.environ["APP_ENV"] = "local"
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        for k, v in saved.items():
            if v is None:
                _os.environ.pop(k, None)
            else:
                _os.environ[k] = v
