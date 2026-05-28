"""API contract tests for project status and auto-phase-advance on task claim."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_task(client, project_id, **kwargs):
    payload = {"title": "Test task", **kwargs}
    return client.post(f"/api/projects/{project_id}/tasks", json=payload).get_json()


def _claim(client, task_id, agent="agent-a"):
    return client.post(f"/api/tasks/{task_id}/claim", json={"agent_name": agent}).get_json()


def _get_statuses(client, project_id):
    return client.get(f"/api/projects/{project_id}/status").get_json()["items"]


class TestProjectStatusCRUD:
    def test_create_status(self, client):
        p = _make_project(client)
        resp = client.post(
            f"/api/projects/{p['id']}/status",
            json={"status": "active", "phase": "implementation", "summary": "underway"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["phase"] == "implementation"
        assert data["source"] is None

    def test_list_statuses(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"})
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        resp = client.get(f"/api/projects/{p['id']}/status")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 2

    def test_invalid_phase_rejected(self, client):
        p = _make_project(client)
        resp = client.post(
            f"/api/projects/{p['id']}/status",
            json={"phase": "planning"},
        )
        assert resp.status_code == 422

    def test_patch_status(self, client):
        p = _make_project(client)
        s = client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"}).get_json()
        resp = client.patch(
            f"/api/projects/{p['id']}/status/{s['id']}",
            json={"summary": "updated", "version": s["version"]},
        )
        assert resp.status_code == 200
        assert resp.get_json()["summary"] == "updated"

    def test_patch_invalid_phase_rejected(self, client):
        p = _make_project(client)
        s = client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"}).get_json()
        resp = client.patch(
            f"/api/projects/{p['id']}/status/{s['id']}",
            json={"phase": "research", "version": s["version"]},
        )
        assert resp.status_code == 422


class TestAutoPhaseAdvance:
    """Claiming a task auto-advances project phase when task phase ordinal > current."""

    def test_no_status_records_created_when_phase_matches(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        task = _make_task(client, p["id"], phase="implementation")
        _claim(client, task["id"])
        statuses = _get_statuses(client, p["id"])
        assert len(statuses) == 1

    def test_advance_creates_new_status_record(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"})
        task = _make_task(client, p["id"], phase="implementation")
        _claim(client, task["id"])
        statuses = _get_statuses(client, p["id"])
        assert len(statuses) == 2
        # Most recent (first in desc order) should be the auto-advanced phase
        assert statuses[0]["phase"] == "implementation"
        assert statuses[0]["source"] == "auto-claim"

    def test_advance_skips_phases(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "discovery"})
        task = _make_task(client, p["id"], phase="testing")
        _claim(client, task["id"])
        statuses = _get_statuses(client, p["id"])
        assert statuses[0]["phase"] == "testing"

    def test_no_advance_when_project_phase_is_higher(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "review"})
        task = _make_task(client, p["id"], phase="implementation")
        _claim(client, task["id"])
        statuses = _get_statuses(client, p["id"])
        assert len(statuses) == 1

    def test_advance_with_no_existing_status(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"], phase="implementation")
        _claim(client, task["id"])
        statuses = _get_statuses(client, p["id"])
        assert len(statuses) == 1
        assert statuses[0]["phase"] == "implementation"
        assert statuses[0]["source"] == "auto-claim"

    def test_no_advance_for_discovery_when_already_discovery(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "discovery"})
        task = _make_task(client, p["id"], phase="discovery")
        _claim(client, task["id"])
        assert len(_get_statuses(client, p["id"])) == 1

    def test_multiple_claims_do_not_duplicate_advance(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"})
        t1 = _make_task(client, p["id"], phase="implementation", title="t1")
        t2 = _make_task(client, p["id"], phase="implementation", title="t2")
        _claim(client, t1["id"], agent="agent-a")
        _claim(client, t2["id"], agent="agent-b")
        statuses = _get_statuses(client, p["id"])
        # Both claims are for the same phase — only one new record on first claim
        impl_records = [s for s in statuses if s["phase"] == "implementation"]
        assert len(impl_records) == 1


class TestPhaseHighWater:
    """Manual phase writes cannot regress below the current high-water mark."""

    def test_create_backward_phase_rejected(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        resp = client.post(f"/api/projects/{p['id']}/status", json={"phase": "design"})
        assert resp.status_code == 422

    def test_create_same_phase_allowed(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        resp = client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        assert resp.status_code == 201

    def test_create_forward_phase_allowed(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "implementation"})
        resp = client.post(f"/api/projects/{p['id']}/status", json={"phase": "review"})
        assert resp.status_code == 201

    def test_patch_backward_phase_rejected(self, client):
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "testing"})
        s = client.post(f"/api/projects/{p['id']}/status", json={"phase": "testing"}).get_json()
        resp = client.patch(
            f"/api/projects/{p['id']}/status/{s['id']}",
            json={"phase": "design", "version": s["version"]},
        )
        assert resp.status_code == 422

    def test_high_water_uses_max_ordinal_not_newest_row(self, client):
        """A lower-phase row added later must not lower the high-water mark."""
        p = _make_project(client)
        client.post(f"/api/projects/{p['id']}/status", json={"phase": "testing"})
        # Simulate a stale row that somehow exists at a lower phase:
        # advance_phase_if_needed won't write it, but create_status would have if called directly.
        # After the fix, we verify the high-water is 'testing', not a lower phase.
        resp = client.post(f"/api/projects/{p['id']}/status", json={"phase": "discovery"})
        assert resp.status_code == 422
