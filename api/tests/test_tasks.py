"""API contract tests for the tasks module — CRUD and lease lifecycle."""
from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_task(client, project_id, **kwargs):
    payload = {"title": "Test task", **kwargs}
    return client.post(f"/api/projects/{project_id}/tasks", json=payload)


class TestListTasks:
    def test_empty(self, client):
        p = _make_project(client)
        resp = client.get(f"/api/projects/{p['id']}/tasks")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_created_task(self, client):
        p = _make_project(client)
        _make_task(client, p["id"])
        resp = client.get(f"/api/projects/{p['id']}/tasks")
        assert resp.get_json()["total"] == 1

    def test_filters_by_status(self, client):
        p = _make_project(client)
        _make_task(client, p["id"], title="pending one")
        resp = client.get(f"/api/projects/{p['id']}/tasks?status=pending")
        assert resp.get_json()["total"] == 1
        resp = client.get(f"/api/projects/{p['id']}/tasks?status=completed")
        assert resp.get_json()["total"] == 0

    def test_404_for_unknown_project(self, client):
        resp = client.get("/api/projects/00000000-0000-0000-0000-000000000000/tasks")
        assert resp.status_code == 404


class TestCreateTask:
    def test_creates_with_title(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"])
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Test task"
        assert data["status"] == "pending"
        assert data["version"] == 1
        assert data["project_id"] == p["id"]

    def test_requires_title(self, client):
        p = _make_project(client)
        resp = client.post(f"/api/projects/{p['id']}/tasks", json={"description": "no title"})
        assert resp.status_code == 422

    def test_stores_optional_fields(self, client):
        p = _make_project(client)
        resp = _make_task(
            client, p["id"],
            description="details",
            priority=5,
            phase="implementation",
            assignee_type="agent",
            assignee_name="claude",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["priority"] == 5
        assert data["phase"] == "implementation"
        assert data["assignee_name"] == "claude"


class TestGetTask:
    def test_returns_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.get(f"/api/tasks/{task['id']}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == task["id"]

    def test_404_for_unknown(self, client):
        resp = client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestUpdateTask:
    def test_updates_title(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.patch(
            f"/api/tasks/{task['id']}",
            json={"title": "Updated", "version": task["version"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["title"] == "Updated"
        assert data["version"] == 2

    def test_version_conflict(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.patch(
            f"/api/tasks/{task['id']}",
            json={"title": "X", "version": task["version"] + 1},
        )
        assert resp.status_code == 409


class TestTaskLeaseLifecycle:
    def test_claim_sets_claimed_by(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/claim",
            json={"agent_name": "test-agent"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["claimed_by"] == "test-agent"
        assert data["claimed_until"] is not None

    def test_double_claim_by_same_agent_succeeds(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"}
        )
        assert resp.status_code == 200

    def test_claim_by_different_agent_conflicts(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-b"}
        )
        assert resp.status_code == 409

    def test_heartbeat_extends_lease(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-a"}
        )
        assert resp.status_code == 200

    def test_heartbeat_wrong_agent_conflicts(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-b"}
        )
        assert resp.status_code == 409

    def test_complete_clears_lease(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/complete",
            json={"agent_name": "agent-a", "evidence": "tests passed"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
        assert data["claimed_by"] is None

    def test_complete_wrong_agent_conflicts(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-b"}
        )
        assert resp.status_code == 409

    def test_block_sets_status(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-a", "reason": "waiting on credential"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "blocked"

    def test_claim_requires_agent_name(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={})
        assert resp.status_code == 422
