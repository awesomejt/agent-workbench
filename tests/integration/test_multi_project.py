"""
Multi-project isolation, lease expiry, and concurrent claim tests.

These require a live HTTP server because they rely on real time-based lease
expiry and actual concurrent TCP connections — scenarios the Flask test client
cannot fully replicate.
"""

from __future__ import annotations

import threading
import time
import uuid

import requests

from conftest import BASE_URL


def _new_project() -> dict:
    slug = f"itest-{uuid.uuid4().hex[:10]}"
    resp = requests.post(f"{BASE_URL}/api/projects", json={"name": slug, "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _task(project_id: str, **kwargs) -> dict:
    resp = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/tasks",
        json={"title": "test task", **kwargs},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestMultiProjectIsolation:
    def test_task_list_scoped_to_project(self, project):
        proj_b = _new_project()

        _task(project["id"], title="Task A")
        _task(proj_b["id"], title="Task B")

        titles_a = [
            t["title"]
            for t in requests.get(
                f"{BASE_URL}/api/projects/{project['id']}/tasks"
            ).json()["items"]
        ]
        titles_b = [
            t["title"]
            for t in requests.get(
                f"{BASE_URL}/api/projects/{proj_b['id']}/tasks"
            ).json()["items"]
        ]

        assert "Task A" in titles_a
        assert "Task B" not in titles_a
        assert "Task B" in titles_b
        assert "Task A" not in titles_b

    def test_available_filter_scoped_to_project(self, project):
        proj_b = _new_project()

        task_a = _task(project["id"])
        task_b = _task(proj_b["id"])

        # Claim task_b so it is no longer available
        requests.post(
            f"{BASE_URL}/api/tasks/{task_b['id']}/claim",
            json={"agent_name": "agent-x"},
        )

        available_a = requests.get(
            f"{BASE_URL}/api/projects/{project['id']}/tasks?available=true"
        ).json()["total"]
        available_b = requests.get(
            f"{BASE_URL}/api/projects/{proj_b['id']}/tasks?available=true"
        ).json()["total"]

        assert available_a == 1   # task_a still available
        assert available_b == 0   # task_b is claimed

        # Unused variable suppression
        _ = task_a


class TestLeaseExpiry:
    def test_short_lease_allows_reclaim_by_different_agent(self, project):
        task = _task(project["id"])

        # Claim with a 1-second lease
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha", "duration_seconds": 1},
        )
        assert resp.status_code == 200
        assert resp.json()["lease_version"] == 1

        time.sleep(3)  # let the 1-second lease expire with margin

        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-beta"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["claimed_by"] == "agent-beta"
        assert data["lease_version"] == 2

    def test_active_lease_blocks_reclaim(self, project):
        task = _task(project["id"])

        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha"},
        )

        # Immediate second claim must fail — lease is still active
        resp = requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-beta"},
        )
        assert resp.status_code == 409

    def test_expired_lease_visible_in_available_filter(self, project):
        task = _task(project["id"])

        requests.post(
            f"{BASE_URL}/api/tasks/{task['id']}/claim",
            json={"agent_name": "agent-alpha", "duration_seconds": 1},
        )

        # While lease is active the task is not available
        assert (
            requests.get(
                f"{BASE_URL}/api/projects/{project['id']}/tasks?available=true"
            ).json()["total"]
            == 0
        )

        time.sleep(2)

        # After expiry it reappears in the available list
        assert (
            requests.get(
                f"{BASE_URL}/api/projects/{project['id']}/tasks?available=true"
            ).json()["total"]
            == 1
        )


class TestConcurrentClaim:
    def test_exactly_one_winner(self, project):
        task = _task(project["id"])
        task_id = task["id"]

        status_codes: list[int] = []
        errors: list[Exception] = []
        barrier = threading.Barrier(2)

        def claim(agent_name: str) -> None:
            try:
                barrier.wait(timeout=5)
                resp = requests.post(
                    f"{BASE_URL}/api/tasks/{task_id}/claim",
                    json={"agent_name": agent_name},
                )
                status_codes.append(resp.status_code)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        t1 = threading.Thread(target=claim, args=("agent-alpha",))
        t2 = threading.Thread(target=claim, args=("agent-beta",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"thread errors: {errors}"
        assert sorted(status_codes) == [200, 409], (
            f"expected exactly one winner (200) and one loser (409), got {status_codes}"
        )

    def test_winner_owns_lease(self, project):
        task = _task(project["id"])
        task_id = task["id"]

        winners: list[str] = []
        barrier = threading.Barrier(2)

        def claim(agent_name: str) -> None:
            barrier.wait(timeout=5)
            resp = requests.post(
                f"{BASE_URL}/api/tasks/{task_id}/claim",
                json={"agent_name": agent_name},
            )
            if resp.status_code == 200:
                winners.append(resp.json()["claimed_by"])

        t1 = threading.Thread(target=claim, args=("agent-alpha",))
        t2 = threading.Thread(target=claim, args=("agent-beta",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert len(winners) == 1
        assert winners[0] in ("agent-alpha", "agent-beta")

        # Verify the stored state matches
        stored = requests.get(f"{BASE_URL}/api/tasks/{task_id}").json()
        assert stored["claimed_by"] == winners[0]
