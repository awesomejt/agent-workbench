FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy application source and migration config
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .

CMD ["uv", "run", "agent-workbench-api"]
