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
            client,
            p["id"],
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

    def test_stores_estimated_duration_seconds(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"], estimated_duration_seconds=3600)
        assert resp.status_code == 201
        assert resp.get_json()["estimated_duration_seconds"] == 3600

    def test_estimated_duration_seconds_defaults_to_null(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"])
        assert resp.get_json()["estimated_duration_seconds"] is None


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
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 200

    def test_claim_by_different_agent_conflicts(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-b"})
        assert resp.status_code == 409

    def test_heartbeat_extends_lease(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-a"})
        assert resp.status_code == 200

    def test_heartbeat_wrong_agent_conflicts(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-b"})
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
        resp = client.post(f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-b"})
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

    def test_claim_uses_task_estimated_duration(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"], estimated_duration_seconds=7200).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-a"},
        )
        assert resp.status_code == 200
        # claimed_until should be ~2 hours from now (not the 30-min default)
        from datetime import UTC, datetime, timedelta

        claimed_until = datetime.fromisoformat(resp.get_json()["claimed_until"])
        delta = claimed_until - datetime.now(UTC)
        assert timedelta(hours=1, minutes=50) < delta < timedelta(hours=2, minutes=10)

    def test_claim_request_duration_overrides_task_estimate(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"], estimated_duration_seconds=7200).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-a", "duration_seconds": 300},
        )
        assert resp.status_code == 200
        from datetime import UTC, datetime, timedelta

        claimed_until = datetime.fromisoformat(resp.get_json()["claimed_until"])
        delta = claimed_until - datetime.now(UTC)
        assert timedelta(minutes=4) < delta < timedelta(minutes=6)

    def test_claim_requires_agent_name(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={})
        assert resp.status_code == 422

    def test_block_clears_lease(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-a", "reason": "blocked"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "blocked"
        assert data["claimed_by"] is None
        assert data["claimed_until"] is None

    def test_duration_seconds_zero_rejected(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-a", "duration_seconds": 0},
        )
        assert resp.status_code == 422

    def test_duration_seconds_negative_rejected(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-a", "duration_seconds": -60},
        )
        assert resp.status_code == 422


class TestTaskEventAutoAppend:
    def _events(self, client, project_id: str) -> list:
        return client.get(f"/api/projects/{project_id}/events").get_json()["items"]

    def test_claim_creates_event(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        events = self._events(client, p["id"])
        assert any(e["event_type"] == "task.claimed" for e in events)

    def test_heartbeat_creates_event(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-a"})
        events = self._events(client, p["id"])
        assert any(e["event_type"] == "task.heartbeat" for e in events)

    def test_complete_creates_event(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-a"})
        events = self._events(client, p["id"])
        assert any(e["event_type"] == "task.completed" for e in events)

    def test_block_creates_event(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(
            f"/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-a", "reason": "waiting"},
        )
        events = self._events(client, p["id"])
        assert any(e["event_type"] == "task.blocked" for e in events)

    def test_event_actor_name_matches_agent(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "my-bot"})
        events = self._events(client, p["id"])
        claimed = next(e for e in events if e["event_type"] == "task.claimed")
        assert claimed["actor_name"] == "my-bot"


class TestTaskEnumValidation:
    def test_invalid_status_on_create_rejected(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"], status="unknown")
        assert resp.status_code == 422

    def test_valid_status_on_create_accepted(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"], status="pending")
        assert resp.status_code == 201

    def test_invalid_phase_on_create_rejected(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"], phase="unknown")
        assert resp.status_code == 422

    def test_valid_phase_on_create_accepted(self, client):
        p = _make_project(client)
        resp = _make_task(client, p["id"], phase="implementation")
        assert resp.status_code == 201

    def test_invalid_status_on_update_rejected(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.patch(
            f"/api/tasks/{task['id']}",
            json={"status": "bogus", "version": task["version"]},
        )
        assert resp.status_code == 422


class TestTaskStateMachineGuards:
    """State machine: invalid transitions must be rejected at the API level."""

    def test_cannot_claim_completed_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-a"})
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 409

    def test_cannot_claim_blocked_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(
            f"/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-a", "reason": "stuck"},
        )
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 409

    def test_cannot_complete_unclaimed_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-a"}
        )
        assert resp.status_code == 409

    def test_cannot_block_unclaimed_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        resp = client.post(
            f"/api/tasks/{task['id']}/block", json={"agent_name": "agent-a"}
        )
        assert resp.status_code == 409

    def test_complete_sets_status_to_completed(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/complete",
            json={"agent_name": "agent-a", "evidence": "all tests pass"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
        assert data["completion_evidence"] == "all tests pass"

    def test_block_sets_status_to_blocked(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(
            f"/api/tasks/{task['id']}/block",
            json={"agent_name": "agent-a", "reason": "waiting for dep"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "blocked"


class TestAvailableFilter:
    """available=true returns only pending tasks with no active lease."""

    def test_available_excludes_claimed_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        assert resp.get_json()["total"] == 0

    def test_available_includes_unclaimed_pending(self, client):
        p = _make_project(client)
        _make_task(client, p["id"])
        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        assert resp.get_json()["total"] == 1

    def test_available_excludes_completed_task(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"]).get_json()
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        client.post(f"/api/tasks/{task['id']}/complete", json={"agent_name": "agent-a"})
        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        assert resp.get_json()["total"] == 0
