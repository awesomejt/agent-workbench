"""API contract tests for the runs module."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_run(client, project_id: str, **kwargs):
    payload = {"project_id": project_id, "agent_name": "test-agent", **kwargs}
    return client.post("/api/runs", json=payload)


def _events(client, project_id: str) -> list:
    return client.get(f"/api/projects/{project_id}/events").get_json()["items"]


class TestCreateRun:
    def test_creates_run(self, client):
        p = _make_project(client)
        resp = _make_run(client, p["id"])
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "running"
        assert data["agent_name"] == "test-agent"
        assert data["project_id"] == p["id"]

    def test_requires_project_id(self, client):
        resp = client.post("/api/runs", json={"agent_name": "bot"})
        assert resp.status_code == 422

    def test_requires_agent_name(self, client):
        p = _make_project(client)
        resp = client.post("/api/runs", json={"project_id": p["id"]})
        assert resp.status_code == 422

    def test_invalid_project_id_rejected(self, client):
        resp = client.post("/api/runs", json={"project_id": "not-a-uuid", "agent_name": "bot"})
        assert resp.status_code == 400

    def test_unknown_project_rejected(self, client):
        resp = client.post(
            "/api/runs",
            json={"project_id": "00000000-0000-0000-0000-000000000000", "agent_name": "bot"},
        )
        assert resp.status_code == 422

    def test_task_id_wrong_project_rejected(self, client):
        p1 = _make_project(client, slug="p1")
        p2 = _make_project(client, slug="p2")
        task = client.post(f"/api/projects/{p1['id']}/tasks", json={"title": "t"}).get_json()
        resp = client.post(
            "/api/runs",
            json={"project_id": p2["id"], "agent_name": "bot", "task_id": task["id"]},
        )
        assert resp.status_code == 422

    def test_task_id_same_project_accepted(self, client):
        p = _make_project(client)
        task = client.post(f"/api/projects/{p['id']}/tasks", json={"title": "t"}).get_json()
        resp = client.post(
            "/api/runs",
            json={"project_id": p["id"], "agent_name": "bot", "task_id": task["id"]},
        )
        assert resp.status_code == 201


class TestGetRun:
    def test_returns_run(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.get(f"/api/runs/{run['id']}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == run["id"]

    def test_404_for_unknown(self, client):
        resp = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestRunStateTransitions:
    def test_heartbeat_updates_run(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.post(f"/api/runs/{run['id']}/heartbeat")
        assert resp.status_code == 200
        assert resp.get_json()["last_heartbeat_at"] is not None

    def test_complete_sets_status(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.post(
            f"/api/runs/{run['id']}/complete",
            json={"summary": "all done"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_fail_sets_status(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.post(f"/api/runs/{run['id']}/fail", json={"summary": "crashed"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "failed"

    def test_heartbeat_on_completed_run_conflicts(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        client.post(f"/api/runs/{run['id']}/complete")
        resp = client.post(f"/api/runs/{run['id']}/heartbeat")
        assert resp.status_code == 409

    def test_complete_on_failed_run_conflicts(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        client.post(f"/api/runs/{run['id']}/fail")
        resp = client.post(f"/api/runs/{run['id']}/complete")
        assert resp.status_code == 409


class TestRunEventAutoAppend:
    def test_heartbeat_creates_event(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        client.post(f"/api/runs/{run['id']}/heartbeat")
        events = _events(client, p["id"])
        assert any(e["event_type"] == "run.heartbeat" for e in events)

    def test_complete_creates_event(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        client.post(f"/api/runs/{run['id']}/complete", json={"summary": "done"})
        events = _events(client, p["id"])
        assert any(e["event_type"] == "run.completed" for e in events)

    def test_fail_creates_event(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        client.post(f"/api/runs/{run['id']}/fail", json={"summary": "crash"})
        events = _events(client, p["id"])
        assert any(e["event_type"] == "run.failed" for e in events)

    def test_event_actor_name_matches_agent(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"], agent_name="my-runner").get_json()
        client.post(f"/api/runs/{run['id']}/complete")
        events = _events(client, p["id"])
        ev = next(e for e in events if e["event_type"] == "run.completed")
        assert ev["actor_name"] == "my-runner"


class TestRuntimeMetrics:
    """Runtime metrics (model_id, tokens, latency, category) can be set on create or complete."""

    def test_metrics_null_by_default(self, client):
        p = _make_project(client)
        data = _make_run(client, p["id"]).get_json()
        assert data["model_id"] is None
        assert data["prompt_tokens"] is None
        assert data["completion_tokens"] is None
        assert data["latency_ms"] is None
        assert data["prompt_category"] is None

    def test_metrics_stored_on_create(self, client):
        p = _make_project(client)
        resp = _make_run(
            client,
            p["id"],
            model_id="claude-sonnet-4-6",
            prompt_tokens=1200,
            completion_tokens=450,
            latency_ms=3200,
            prompt_category="code",
        )
        data = resp.get_json()
        assert data["model_id"] == "claude-sonnet-4-6"
        assert data["prompt_tokens"] == 1200
        assert data["completion_tokens"] == 450
        assert data["latency_ms"] == 3200
        assert data["prompt_category"] == "code"

    def test_metrics_stored_on_complete(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.post(
            f"/api/runs/{run['id']}/complete",
            json={
                "model_id": "claude-sonnet-4-6",
                "prompt_tokens": 800,
                "completion_tokens": 300,
                "latency_ms": 1500,
                "prompt_category": "review",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["model_id"] == "claude-sonnet-4-6"
        assert data["prompt_tokens"] == 800
        assert data["completion_tokens"] == 300
        assert data["latency_ms"] == 1500
        assert data["prompt_category"] == "review"

    def test_metrics_stored_on_fail(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"]).get_json()
        resp = client.post(
            f"/api/runs/{run['id']}/fail",
            json={"model_id": "claude-haiku-4-5", "prompt_tokens": 200},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["model_id"] == "claude-haiku-4-5"
        assert data["prompt_tokens"] == 200
        assert data["completion_tokens"] is None

    def test_complete_overwrites_metrics_set_at_create(self, client):
        p = _make_project(client)
        run = _make_run(client, p["id"], model_id="claude-haiku-4-5", prompt_tokens=100).get_json()
        resp = client.post(
            f"/api/runs/{run['id']}/complete",
            json={"model_id": "claude-sonnet-4-6", "prompt_tokens": 900},
        )
        data = resp.get_json()
        assert data["model_id"] == "claude-sonnet-4-6"
        assert data["prompt_tokens"] == 900
