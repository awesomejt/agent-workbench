"""API contract tests for the reviews module."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_task(client, project_id, title="task"):
    return client.post(
        f"/api/projects/{project_id}/tasks", json={"title": title}
    ).get_json()


def _make_review(client, project_id, **kwargs):
    payload = {"finding": "Something to investigate", **kwargs}
    return client.post(f"/api/projects/{project_id}/reviews", json=payload)


class TestCreateReview:
    def test_creates_review(self, client):
        p = _make_project(client)
        resp = _make_review(client, p["id"])
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["finding"] == "Something to investigate"
        assert data["project_id"] == p["id"]

    def test_requires_finding(self, client):
        p = _make_project(client)
        resp = client.post(f"/api/projects/{p['id']}/reviews", json={"severity": "low"})
        assert resp.status_code == 422

    def test_invalid_severity_rejected(self, client):
        p = _make_project(client)
        resp = _make_review(client, p["id"], severity="extreme")
        assert resp.status_code == 422

    def test_invalid_status_rejected(self, client):
        p = _make_project(client)
        resp = _make_review(client, p["id"], status="published")
        assert resp.status_code == 422

    def test_linked_task_id_nonexistent_rejected(self, client):
        p = _make_project(client)
        resp = _make_review(
            client, p["id"], linked_task_id="00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 422

    def test_linked_task_id_cross_project_rejected(self, client):
        p1 = _make_project(client, slug="p1")
        p2 = _make_project(client, slug="p2")
        task = _make_task(client, p1["id"])
        resp = _make_review(client, p2["id"], linked_task_id=task["id"])
        assert resp.status_code == 422

    def test_linked_task_id_same_project_accepted(self, client):
        p = _make_project(client)
        task = _make_task(client, p["id"])
        resp = _make_review(client, p["id"], linked_task_id=task["id"])
        assert resp.status_code == 201
        assert resp.get_json()["linked_task_id"] == task["id"]


class TestUpdateReview:
    def test_linked_task_id_cross_project_rejected_on_update(self, client):
        p1 = _make_project(client, slug="p1")
        p2 = _make_project(client, slug="p2")
        task_p2 = _make_task(client, p2["id"])
        review = _make_review(client, p1["id"]).get_json()
        resp = client.patch(
            f"/api/reviews/{review['id']}",
            json={"linked_task_id": task_p2["id"], "version": review["version"]},
        )
        assert resp.status_code == 422
