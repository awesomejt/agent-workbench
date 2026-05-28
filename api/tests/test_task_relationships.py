"""API contract tests for task relationships (blocks, subtask_of, duplicates, relates_to)."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_task(client, project_id, **kwargs):
    payload = {"title": "Test task", **kwargs}
    return client.post(f"/api/projects/{project_id}/tasks", json=payload).get_json()


def _make_rel(client, from_task_id, to_task_id, rel_type="relates_to"):
    return client.post(
        f"/api/tasks/{from_task_id}/relationships",
        json={"to_task_id": to_task_id, "relationship_type": rel_type},
    )


class TestListRelationships:
    def test_empty_list(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        resp = client.get(f"/api/tasks/{t['id']}/relationships")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_outgoing_relationship(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="from")
        t2 = _make_task(client, p["id"], title="to")
        _make_rel(client, t1["id"], t2["id"])
        resp = client.get(f"/api/tasks/{t1['id']}/relationships")
        assert resp.get_json()["total"] == 1

    def test_returns_incoming_relationship(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="from")
        t2 = _make_task(client, p["id"], title="to")
        _make_rel(client, t1["id"], t2["id"])
        # t2 should also see the relationship (incoming)
        resp = client.get(f"/api/tasks/{t2['id']}/relationships")
        assert resp.get_json()["total"] == 1

    def test_404_for_unknown_task(self, client):
        resp = client.get("/api/tasks/00000000-0000-0000-0000-000000000000/relationships")
        assert resp.status_code == 404


class TestCreateRelationship:
    def test_creates_relates_to(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        resp = _make_rel(client, t1["id"], t2["id"], "relates_to")
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["from_task_id"] == t1["id"]
        assert data["to_task_id"] == t2["id"]
        assert data["relationship_type"] == "relates_to"

    def test_creates_blocks(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        resp = _make_rel(client, t1["id"], t2["id"], "blocks")
        assert resp.status_code == 201

    def test_creates_subtask_of(self, client):
        p = _make_project(client)
        parent = _make_task(client, p["id"], title="parent")
        child = _make_task(client, p["id"], title="child")
        resp = _make_rel(client, child["id"], parent["id"], "subtask_of")
        assert resp.status_code == 201

    def test_creates_duplicates(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        resp = _make_rel(client, t1["id"], t2["id"], "duplicates")
        assert resp.status_code == 201

    def test_invalid_relationship_type_rejected(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        resp = _make_rel(client, t1["id"], t2["id"], "unknown_type")
        assert resp.status_code == 422

    def test_missing_to_task_id_rejected(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        resp = client.post(
            f"/api/tasks/{t['id']}/relationships",
            json={"relationship_type": "relates_to"},
        )
        assert resp.status_code == 422

    def test_missing_relationship_type_rejected(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        resp = client.post(
            f"/api/tasks/{t1['id']}/relationships",
            json={"to_task_id": t2["id"]},
        )
        assert resp.status_code == 422

    def test_self_relationship_rejected(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        resp = _make_rel(client, t["id"], t["id"])
        assert resp.status_code == 422

    def test_cross_project_relationship_rejected(self, client):
        p1 = _make_project(client, slug="proj-a")
        p2 = _make_project(client, slug="proj-b")
        t1 = _make_task(client, p1["id"])
        t2 = _make_task(client, p2["id"])
        resp = _make_rel(client, t1["id"], t2["id"])
        assert resp.status_code == 422

    def test_duplicate_relationship_rejected(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        _make_rel(client, t1["id"], t2["id"])
        resp = _make_rel(client, t1["id"], t2["id"])
        assert resp.status_code == 409

    def test_404_for_unknown_to_task(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        resp = client.post(
            f"/api/tasks/{t['id']}/relationships",
            json={
                "to_task_id": "00000000-0000-0000-0000-000000000000",
                "relationship_type": "relates_to",
            },
        )
        assert resp.status_code == 404


class TestDeleteRelationship:
    def test_deletes_relationship(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        rel = _make_rel(client, t1["id"], t2["id"]).get_json()
        resp = client.delete(f"/api/tasks/{t1['id']}/relationships/{rel['id']}")
        assert resp.status_code == 204
        # Confirm gone
        resp2 = client.get(f"/api/tasks/{t1['id']}/relationships")
        assert resp2.get_json()["total"] == 0

    def test_delete_via_to_task(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        rel = _make_rel(client, t1["id"], t2["id"]).get_json()
        resp = client.delete(f"/api/tasks/{t2['id']}/relationships/{rel['id']}")
        assert resp.status_code == 204

    def test_404_for_unknown_relationship(self, client):
        p = _make_project(client)
        t = _make_task(client, p["id"])
        resp = client.delete(
            f"/api/tasks/{t['id']}/relationships/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404

    def test_404_when_task_not_party_to_relationship(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"])
        t2 = _make_task(client, p["id"])
        t3 = _make_task(client, p["id"])
        rel = _make_rel(client, t1["id"], t2["id"]).get_json()
        # t3 is not part of this relationship
        resp = client.delete(f"/api/tasks/{t3['id']}/relationships/{rel['id']}")
        assert resp.status_code == 404


class TestBlocksAvailableFilter:
    """tasks blocked by incomplete 'blocks' predecessors are excluded from available=true."""

    def _claim(self, client, task_id):
        return client.post(f"/api/tasks/{task_id}/claim", json={"agent_name": "agent-a"})

    def _complete(self, client, task_id):
        return client.post(f"/api/tasks/{task_id}/complete", json={"agent_name": "agent-a"})

    def test_blocked_task_excluded_from_available(self, client):
        p = _make_project(client)
        blocker = _make_task(client, p["id"], title="blocker")
        dependent = _make_task(client, p["id"], title="dependent")
        _make_rel(client, blocker["id"], dependent["id"], "blocks")

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        available_ids = {t["id"] for t in resp.get_json()["items"]}
        assert dependent["id"] not in available_ids
        assert blocker["id"] in available_ids  # blocker itself is available

    def test_blocked_task_available_after_blocker_completes(self, client):
        p = _make_project(client)
        blocker = _make_task(client, p["id"], title="blocker")
        dependent = _make_task(client, p["id"], title="dependent")
        _make_rel(client, blocker["id"], dependent["id"], "blocks")

        # Complete the blocker
        self._claim(client, blocker["id"])
        self._complete(client, blocker["id"])

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        available_ids = {t["id"] for t in resp.get_json()["items"]}
        assert dependent["id"] in available_ids

    def test_relates_to_does_not_block(self, client):
        p = _make_project(client)
        t1 = _make_task(client, p["id"], title="t1")
        t2 = _make_task(client, p["id"], title="t2")
        _make_rel(client, t1["id"], t2["id"], "relates_to")

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        available_ids = {t["id"] for t in resp.get_json()["items"]}
        assert t2["id"] in available_ids  # not blocked

    def test_subtask_of_does_not_block(self, client):
        p = _make_project(client)
        parent = _make_task(client, p["id"], title="parent")
        child = _make_task(client, p["id"], title="child")
        _make_rel(client, child["id"], parent["id"], "subtask_of")

        resp = client.get(f"/api/projects/{p['id']}/tasks?available=true")
        available_ids = {t["id"] for t in resp.get_json()["items"]}
        assert child["id"] in available_ids
        assert parent["id"] in available_ids

    def test_direct_claim_blocked_by_incomplete_predecessor(self, client):
        """POST /api/tasks/{id}/claim must reject tasks with incomplete 'blocks' predecessors."""
        p = _make_project(client)
        blocker = _make_task(client, p["id"], title="blocker")
        dependent = _make_task(client, p["id"], title="dependent")
        _make_rel(client, blocker["id"], dependent["id"], "blocks")

        resp = client.post(f"/api/tasks/{dependent['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 409

    def test_direct_claim_allowed_after_blocker_completes(self, client):
        """Claim succeeds once the blocking predecessor is completed."""
        p = _make_project(client)
        blocker = _make_task(client, p["id"], title="blocker")
        dependent = _make_task(client, p["id"], title="dependent")
        _make_rel(client, blocker["id"], dependent["id"], "blocks")

        # Complete the blocker first
        client.post(f"/api/tasks/{blocker['id']}/claim", json={"agent_name": "agent-a"})
        client.post(f"/api/tasks/{blocker['id']}/complete", json={"agent_name": "agent-a"})

        resp = client.post(f"/api/tasks/{dependent['id']}/claim", json={"agent_name": "agent-a"})
        assert resp.status_code == 200
