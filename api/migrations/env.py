from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic autogenerate can detect them
from agent_workbench.agents.models import Agent  # noqa: F401, E402
from agent_workbench.database import db  # noqa: E402
from agent_workbench.events.models import Event  # noqa: F401, E402
from agent_workbench.idempotency.models import IdempotencyRecord  # noqa: F401, E402
from agent_workbench.project_sections.models import ProjectSection  # noqa: F401, E402
from agent_workbench.project_status.models import ProjectStatus  # noqa: F401, E402
from agent_workbench.projects.models import Project  # noqa: F401, E402
from agent_workbench.reviews.models import Review  # noqa: F401, E402
from agent_workbench.runs.models import Run  # noqa: F401, E402
from agent_workbench.tasks.models import Task  # noqa: F401, E402

target_metadata = db.metadata

SCHEMA = "agent_workbench"

_ENV_VAR_MAP = {
    "local": "AGENT_WORKBENCH_LOCAL_DATABASE_URL",
    "dev": "AGENT_WORKBENCH_DEV_DATABASE_URL",
    "stage": "AGENT_WORKBENCH_STAGE_DATABASE_URL",
    "prod": "AGENT_WORKBENCH_PROD_DATABASE_URL",
}


def get_url() -> str:
    app_env = os.environ.get("APP_ENV", "local")
    env_var = _ENV_VAR_MAP.get(app_env, "AGENT_WORKBENCH_LOCAL_DATABASE_URL")
    url = os.environ.get(env_var) or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            f"No database URL configured for APP_ENV={app_env!r}. "
            f"Set {env_var} or DATABASE_URL."
        )
    return url


def _include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == SCHEMA
    return True


def _configure_context(connection, **kwargs):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_name=_include_name,
        compare_type=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_name=_include_name,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        connection.execute(text(f"CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        connection.execute(text(f"SET search_path TO {SCHEMA}, public"))
        connection.commit()
        _configure_context(connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
