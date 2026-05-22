"""API contract tests for the agents module."""
from __future__ import annotations


def _create(client, name="test-agent", **kwargs):
    return client.post("/api/agents", json={"name": name, "agent_type": "cli", **kwargs})


class TestListAgents:
    def test_empty(self, client):
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_created_agent(self, client):
        _create(client)
        resp = client.get("/api/agents")
        assert resp.get_json()["total"] == 1


class TestCreateAgent:
    def test_creates_with_required_fields(self, client):
        resp = _create(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "test-agent"
        assert data["agent_type"] == "cli"
        assert data["version"] == 1

    def test_requires_name(self, client):
        resp = client.post("/api/agents", json={"agent_type": "cli"})
        assert resp.status_code == 422

    def test_defaults_agent_type_to_local(self, client):
        resp = client.post("/api/agents", json={"name": "no-type-agent"})
        assert resp.status_code == 201
        assert resp.get_json()["agent_type"] == "local"

    def test_name_unique(self, client):
        _create(client)
        resp = _create(client)
        assert resp.status_code == 409

    def test_stores_optional_fields(self, client):
        resp = _create(
            client,
            default_model="claude-sonnet-4-6",
            runtime_notes="runs locally",
            capabilities={"can_write_files": True},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["default_model"] == "claude-sonnet-4-6"
        assert data["capabilities"] == {"can_write_files": True}


class TestGetAgent:
    def test_returns_agent(self, client):
        agent_id = _create(client).get_json()["id"]
        resp = client.get(f"/api/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == agent_id

    def test_404_for_unknown(self, client):
        resp = client.get("/api/agents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_400_for_invalid_uuid(self, client):
        resp = client.get("/api/agents/not-a-uuid")
        assert resp.status_code == 400


class TestUpdateAgent:
    def test_updates_runtime_notes(self, client):
        agent = _create(client).get_json()
        resp = client.patch(
            f"/api/agents/{agent['id']}",
            json={"runtime_notes": "updated notes", "version": agent["version"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["runtime_notes"] == "updated notes"
        assert data["version"] == 2

    def test_requires_version(self, client):
        agent = _create(client).get_json()
        resp = client.patch(f"/api/agents/{agent['id']}", json={"runtime_notes": "x"})
        assert resp.status_code == 422

    def test_version_conflict(self, client):
        agent = _create(client).get_json()
        resp = client.patch(
            f"/api/agents/{agent['id']}",
            json={"runtime_notes": "x", "version": agent["version"] + 1},
        )
        assert resp.status_code == 409
