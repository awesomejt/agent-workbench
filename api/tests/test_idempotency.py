"""Tests for idempotency key behavior on task lifecycle endpoints."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_task(client, project_id, **kwargs):
    payload = {"title": "Test task", **kwargs}
    return client.post(f"/api/projects/{project_id}/tasks", json=payload).get_json()


def _claim(client, task_id, agent="agent-a", key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        f"/api/tasks/{task_id}/claim",
        json={"agent_name": agent},
        headers=headers,
    )


def _heartbeat(client, task_id, agent="agent-a", key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        f"/api/tasks/{task_id}/heartbeat",
        json={"agent_name": agent},
        headers=headers,
    )


def _complete(client, task_id, agent="agent-a", key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        f"/api/tasks/{task_id}/complete",
        json={"agent_name": agent, "evidence": "done"},
        headers=headers,
    )


def _block(client, task_id, agent="agent-a", key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        f"/api/tasks/{task_id}/block",
        json={"agent_name": agent, "reason": "stuck"},
        headers=headers,
    )


class TestClaimIdempotency:
    def test_same_key_replays_response(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])

        r1 = _claim(client, t["id"], key="key-abc")
        assert r1.status_code == 200
        first_version = r1.get_json()["version"]

        # Second call with same key — must replay, not re-apply
        r2 = _claim(client, t["id"], key="key-abc")
        assert r2.status_code == 200
        assert r2.get_json()["version"] == first_version

    def test_different_key_is_independent(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="task one")
        t2 = _make_task(client, p["id"], title="task two")

        # Two separate claims with different keys are independent — no replay interference
        r1 = _claim(client, t1["id"], key="key-1")
        r2 = _claim(client, t2["id"], agent="agent-a", key="key-2")
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_without_key_always_processes(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="task one")
        t2 = _make_task(client, p["id"], title="task two")

        # Without a key, requests are never deduplicated — each claim is independent
        r1 = _claim(client, t1["id"])
        r2 = _claim(client, t2["id"])
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_different_agent_same_key_is_independent(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="task one")
        t2 = _make_task(client, p["id"], title="task two")

        # agent-a claims t1 with key-x; agent-b claims t2 with key-x — no conflict
        r1 = _claim(client, t1["id"], agent="agent-a", key="key-x")
        r2 = _claim(client, t2["id"], agent="agent-b", key="key-x")
        assert r1.status_code == 200
        assert r2.status_code == 200


class TestHeartbeatIdempotency:
    def test_same_key_replays_response(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        _claim(client, t["id"])

        r1 = _heartbeat(client, t["id"], key="hb-key")
        assert r1.status_code == 200
        first_until = r1.get_json()["claimed_until"]

        r2 = _heartbeat(client, t["id"], key="hb-key")
        assert r2.status_code == 200
        assert r2.get_json()["claimed_until"] == first_until


class TestCompleteIdempotency:
    def test_same_key_replays_response(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        _claim(client, t["id"])

        r1 = _complete(client, t["id"], key="done-key")
        assert r1.status_code == 200
        first_version = r1.get_json()["version"]

        r2 = _complete(client, t["id"], key="done-key")
        assert r2.status_code == 200
        assert r2.get_json()["version"] == first_version


class TestBlockIdempotency:
    def test_same_key_replays_response(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        _claim(client, t["id"])

        r1 = _block(client, t["id"], key="block-key")
        assert r1.status_code == 200
        first_version = r1.get_json()["version"]

        r2 = _block(client, t["id"], key="block-key")
        assert r2.status_code == 200
        assert r2.get_json()["version"] == first_version
