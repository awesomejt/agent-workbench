"""Tests for the optional Prometheus /metrics endpoint."""

from __future__ import annotations

import os

import pytest

_TEST_DATABASE_URL = os.environ.get(
    "AGENT_WORKBENCH_TEST_DATABASE_URL",
    "postgresql+psycopg://agent_workbench:agent_workbench_local@localhost:5433/agent_workbench_test",
)


@pytest.fixture(scope="module")
def metrics_app():
    from agent_workbench.app import create_app
    from agent_workbench.config import Settings

    settings = Settings(
        app_env="local",
        database_url=_TEST_DATABASE_URL,
        secret_key="test-secret",
        prometheus_enabled=True,
    )
    app = create_app(settings)
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def metrics_client(metrics_app):
    return metrics_app.test_client()


class TestMetricsDisabled:
    def test_returns_404_when_not_enabled(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 404


class TestMetricsEnabled:
    def test_returns_200(self, metrics_client):
        resp = metrics_client.get("/metrics")
        assert resp.status_code == 200

    def test_prometheus_content_type(self, metrics_client):
        resp = metrics_client.get("/metrics")
        assert "text/plain" in resp.content_type

    def test_body_has_help_lines(self, metrics_client):
        resp = metrics_client.get("/metrics")
        assert b"# HELP" in resp.data

    def test_request_counter_present(self, metrics_client):
        metrics_client.get("/health")
        resp = metrics_client.get("/metrics")
        assert b"http_requests_total" in resp.data

    def test_latency_histogram_present(self, metrics_client):
        resp = metrics_client.get("/metrics")
        assert b"http_request_duration_seconds" in resp.data
