"""
Database integration tests.

These tests exercise scenarios that require direct database state manipulation
(expired leases) or concurrent access (simultaneous claims). All tests hit the
same PostgreSQL container used by the rest of the test suite.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta

from flask import Flask
from sqlalchemy import text

from agent_workbench.database import db

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_project(client, slug: str | None = None) -> dict:
    s = slug or f"proj-{uuid.uuid4().hex[:8]}"
    return client.post("/api/projects", json={"name": s, "slug": s}).get_json()


def _make_task(client, project_id: str, **kwargs) -> dict:
    payload = {"title": "Integration test task", **kwargs}
    return client.post(f"/api/projects/{project_id}/tasks", json=payload).get_json()


def _expire_lease(task_id: str) -> None:
    """Move a task's claimed_until one hour into the past via direct SQL."""
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE agent_workbench.tasks SET claimed_until = :ts WHERE id = :id"),
            {"ts": datetime.now(UTC) - timedelta(hours=1), "id": uuid.UUID(task_id)},
        )
        conn.commit()


# ── Expired leases ────────────────────────────────────────────────────────────


class TestExpiredLeases:
    """Tasks with expired leases become available for re-claim."""

    def test_expired_lease_allows_reclaim_by_different_agent(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])

        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 200

        _expire_lease(task["id"])

        resp2 = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-b"})
        assert resp2.status_code == 200
        data = resp2.get_json()
        assert data["claimed_by"] == "agent-b"
        assert data["lease_version"] == 2

    def test_expired_lease_allows_reclaim_by_same_agent(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])

        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        _expire_lease(task["id"])

        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 200
        assert resp.get_json()["lease_version"] == 2

    def test_available_filter_includes_task_with_expired_lease(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])

        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        _expire_lease(task["id"])

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 1

    def test_active_lease_blocks_available_filter(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])

        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        assert resp.get_json()["total"] == 0


# ── Concurrent claims ─────────────────────────────────────────────────────────


class TestConcurrentClaim:
    """PostgreSQL's atomic row-level UPDATE ensures exactly one agent wins."""

    def test_concurrent_claims_exactly_one_wins(self, app: Flask, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        task_id = task["id"]

        results: list[int] = []
        errors: list[Exception] = []
        barrier = threading.Barrier(2)

        def claim(agent_name: str) -> None:
            try:
                barrier.wait(timeout=5)
                with app.test_client() as c:
                    resp = c.post(
                        f"/api/tasks/{task_id}/claim",
                        json={"agent_name": agent_name},
                    )
                    results.append(resp.status_code)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        t1 = threading.Thread(target=claim, args=("agent-a",))
        t2 = threading.Thread(target=claim, args=("agent-b",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        assert sorted(results) == [200, 409], f"Expected [200, 409], got {results}"

    def test_concurrent_claims_winner_owns_lease(self, app: Flask, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        task_id = task["id"]

        agents: list[str] = []
        barrier = threading.Barrier(2)

        def claim(agent_name: str) -> None:
            barrier.wait(timeout=5)
            with app.test_client() as c:
                resp = c.post(
                    f"/api/tasks/{task_id}/claim",
                    json={"agent_name": agent_name},
                )
                if resp.status_code == 200:
                    agents.append(resp.get_json()["claimed_by"])

        t1 = threading.Thread(target=claim, args=("agent-a",))
        t2 = threading.Thread(target=claim, args=("agent-b",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # Exactly one winner; the winner field must match an agent name
        assert len(agents) == 1
        assert agents[0] in ("agent-a", "agent-b")

        # The task now reflects that winner
        resp = client.get(f"/api/tasks/{task_id}")
        assert resp.get_json()["claimed_by"] == agents[0]


# ── Lease version tracking ────────────────────────────────────────────────────


class TestLeaseVersioning:
    """lease_version increments on every successful claim."""

    def test_lease_version_starts_at_zero_before_claim(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        resp = client.get(f"/api/tasks/{task['id']}")
        assert resp.get_json()["lease_version"] == 0

    def test_lease_version_is_one_after_first_claim(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.get_json()["lease_version"] == 1

    def test_lease_version_increments_on_reclaim_after_expiry(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        _expire_lease(task["id"])
        resp = client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-b"})
        assert resp.get_json()["lease_version"] == 2

    def test_heartbeat_does_not_increment_lease_version(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        client.post(f"/api/tasks/{task['id']}/claim", json={"agent_name": "agent-a"})
        resp = client.post(f"/api/tasks/{task['id']}/heartbeat", json={"agent_name": "agent-a"})
        assert resp.get_json()["lease_version"] == 1


# ── Multi-project isolation ───────────────────────────────────────────────────


class TestMultiProjectIsolation:
    """Tasks and status records are scoped strictly to their own project."""

    def test_task_list_scoped_to_project(self, client):
        pa = _make_project(client, "project-a")
        pb = _make_project(client, "project-b")

        _make_task(client, pa["id"], title="Task A")
        _make_task(client, pb["id"], title="Task B")

        titles_a = [
            t["title"] for t in client.get(f"/api/projects/{pa['id']}/tasks").get_json()["items"]
        ]
        titles_b = [
            t["title"] for t in client.get(f"/api/projects/{pb['id']}/tasks").get_json()["items"]
        ]

        assert "Task A" in titles_a
        assert "Task B" not in titles_a
        assert "Task B" in titles_b
        assert "Task A" not in titles_b

    def test_section_id_from_other_project_rejected(self, client):
        pa = _make_project(client, "project-a")
        pb = _make_project(client, "project-b")

        # Create a section in project-b
        section_b = client.post(
            f"/api/projects/{pb['id']}/sections",
            json={"name": "Section B", "slug": "section-b"},
        ).get_json()

        # Trying to create a task in project-a using project-b's section ID must fail
        resp = client.post(
            f"/api/projects/{pa['id']}/tasks",
            json={"title": "Cross-project task", "project_section_id": section_b["id"]},
        )
        assert resp.status_code == 422
