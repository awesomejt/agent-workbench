"""
End-to-end task lifecycle tests against a running API server.

These tests hit real HTTP endpoints. They cover the golden path and key
transitions that the unit tests exercise via the Flask test client.
"""

from __future__ import annotations

import requests

from conftest import BASE_URL


def _task(project_id: str, **kwargs) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/tasks",
        json={"title": "integration test task", **kwargs},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestHealthCheck:
    def test_health_returns_ok(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestFullTaskWorkflow:
    def test_create_claim_heartbeat_complete(self, project):
        task = _task(project["id"], title="golden path task")
        assert task["status"] == "pending"
        assert task["lease_version"] == 0

        # Claim
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )
        assert resp.status_code == 200
        task = resp.json()
        assert task["status"] == "in_progress"
        assert task["claimed_by"] == "agent-alpha"
        assert task["lease_version"] == 1

        # Heartbeat extends the lease
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/heartbeat",
            json={"agent_name": "agent-alpha"},
        )
        assert resp.status_code == 200
        assert resp.json()["lease_version"] == 1  # heartbeat does not bump version

        # Complete
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/complete",
            json={"agent_name": "agent-alpha", "evidence": "https://example.com/pr/1"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_cannot_claim_already_claimed_task(self, project):
        task = _task(project["id"])
        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-beta"},
        )
        assert resp.status_code == 409

    def test_block_and_unblock(self, project):
        task = _task(project["id"], title="blockable task")

        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )

        # Block
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-alpha", "reason": "waiting on upstream dependency"},
        )
        assert resp.status_code == 200
        blocked = resp.json()
        assert blocked["status"] == "blocked"

        # Unblock via PATCH (blocked → pending is a valid PATCH transition)
        resp = requests.patch(
            f"{BASE_URL}/api/tasks/{task['id']}",
            json={"status": "pending", "version": blocked["version"]},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

        # Re-claim after unblock
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-beta"},
        )
        assert resp.status_code == 200
        assert resp.json()["claimed_by"] == "agent-beta"


class TestRunLifecycle:
    def test_run_create_heartbeat_complete(self, project):
        task = _task(project["id"])
        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )

        # Start run
        resp = requests.post(
            f"{BASE_URL}/api/runs",
            json={
                "project_id": project["id"],
                "task_id": task["id"],
                "agent_name": "agent-alpha",
                "summary": "integration test run",
            },
        )
        assert resp.status_code == 201
        run = resp.json()
        assert run["status"] == "running"

        # Heartbeat
        resp = requests.post(f"{BASE_URL}/api/runs/{run['id']}/heartbeat")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

        # Complete
        resp = requests.post(
            f"{BASE_URL}/api/runs/{run['id']}/complete",
            json={"summary": "all steps passed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_run_fail(self, project):
        task = _task(project["id"])
        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )
        run = requests.post(
            f"{BASE_URL}/api/runs",
            json={"project_id": project["id"], "agent_name": "agent-alpha"},
        ).json()

        resp = requests.post(
            f"{BASE_URL}/api/runs/{run['id']}/fail",
            json={"summary": "unrecoverable error"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"


class TestEventAppend:
    def test_events_visible_after_append(self, project):
        task = _task(project["id"])

        resp = requests.post(
            f"{BASE_URL}/api/events",
            json={
                "project_id": project["id"],
                "task_id": task["id"],
                "event_type": "note",
                "summary": "integration test event",
            },
        )
        assert resp.status_code == 201

        events = requests.get(f"{BASE_URL}/api/projects/{project['id']}/events").json()
        assert events["total"] >= 1
        types = [e["event_type"] for e in events["items"]]
        assert "note" in types
