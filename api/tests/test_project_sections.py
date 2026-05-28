"""API contract tests for project sections."""

from __future__ import annotations


def _make_project(client, slug="proj"):
    return client.post("/api/projects", json={"name": slug, "slug": slug}).get_json()


def _make_section(client, project_id, slug="sec", **kwargs):
    payload = {"name": slug.capitalize(), "slug": slug, **kwargs}
    return client.post(f"/api/projects/{project_id}/sections", json=payload)


class TestCreateSection:
    def test_creates_section(self, client):
        p = _make_project(client)
        resp = _make_section(client, p["id"])
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["slug"] == "sec"
        assert data["project_id"] == p["id"]

    def test_duplicate_slug_within_project_rejected(self, client):
        p = _make_project(client)
        _make_section(client, p["id"], slug="dup")
        resp = _make_section(client, p["id"], slug="dup")
        assert resp.status_code == 409

    def test_same_slug_in_different_projects_allowed(self, client):
        p1 = _make_project(client, slug="proj-a")
        p2 = _make_project(client, slug="proj-b")
        r1 = _make_section(client, p1["id"], slug="shared")
        r2 = _make_section(client, p2["id"], slug="shared")
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_requires_name_and_slug(self, client):
        p = _make_project(client)
        resp = client.post(f"/api/projects/{p['id']}/sections", json={"name": "no slug"})
        assert resp.status_code == 422
