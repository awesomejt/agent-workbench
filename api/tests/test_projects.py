"""API contract tests for the projects module."""

from __future__ import annotations


def _create(client, **kwargs):
    payload = {"name": "Test Project", "slug": "test-project", **kwargs}
    return client.post("/api/projects", json=payload)


class TestListProjects:
    def test_empty(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_returns_created_project(self, client):
        _create(client)
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 1

    def test_pagination(self, client):
        for i in range(3):
            _create(client, name=f"P{i}", slug=f"p{i}")
        resp = client.get("/api/projects?per_page=2&page=1")
        data = resp.get_json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2


class TestCreateProject:
    def test_creates_with_required_fields(self, client):
        resp = _create(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["slug"] == "test-project"
        assert data["version"] == 1
        assert "id" in data

    def test_requires_name(self, client):
        resp = client.post("/api/projects", json={"slug": "no-name"})
        assert resp.status_code == 422

    def test_requires_slug(self, client):
        resp = client.post("/api/projects", json={"name": "No Slug"})
        assert resp.status_code == 422

    def test_slug_unique(self, client):
        _create(client)
        resp = _create(client)
        assert resp.status_code == 409

    def test_stores_optional_fields(self, client):
        resp = _create(
            client,
            project_type="code",
            environment="dev",
            git_remote_url="https://github.com/example/repo",
            local_path="/home/user/repo",
            default_agent="claude",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["project_type"] == "code"
        assert data["environment"] == "dev"
        assert data["git_remote_url"] == "https://github.com/example/repo"

    def test_all_valid_project_types_accepted(self, client):
        for i, pt in enumerate(
            ["code", "course", "content", "research", "infrastructure", "other"]
        ):
            resp = _create(client, name=f"p-{i}", slug=f"slug-{i}", project_type=pt)
            assert resp.status_code == 201, f"Expected 201 for project_type={pt}"

    def test_invalid_project_type_rejected(self, client):
        resp = _create(client, project_type="library")
        assert resp.status_code == 422

    def test_default_project_type_is_code(self, client):
        resp = _create(client)
        assert resp.status_code == 201
        assert resp.get_json()["project_type"] == "code"


class TestGetProject:
    def test_returns_project(self, client):
        project_id = _create(client).get_json()["id"]
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == project_id

    def test_404_for_unknown(self, client):
        resp = client.get("/api/projects/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_400_for_invalid_uuid(self, client):
        resp = client.get("/api/projects/not-a-uuid")
        assert resp.status_code == 400


class TestUpdateProject:
    def test_updates_name(self, client):
        project = _create(client).get_json()
        resp = client.patch(
            f"/api/projects/{project['id']}",
            json={"name": "Updated Name", "version": project["version"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "Updated Name"
        assert data["version"] == 2

    def test_requires_version(self, client):
        project = _create(client).get_json()
        resp = client.patch(f"/api/projects/{project['id']}", json={"name": "New Name"})
        assert resp.status_code == 422

    def test_version_conflict(self, client):
        project = _create(client).get_json()
        resp = client.patch(
            f"/api/projects/{project['id']}",
            json={"name": "Name", "version": project["version"] + 1},
        )
        assert resp.status_code == 409

    def test_slug_conflict_on_update(self, client):
        _create(client, name="A", slug="slug-a")
        b = _create(client, name="B", slug="slug-b").get_json()
        resp = client.patch(
            f"/api/projects/{b['id']}",
            json={"slug": "slug-a", "version": b["version"]},
        )
        assert resp.status_code == 409

    def test_404_for_unknown(self, client):
        resp = client.patch(
            "/api/projects/00000000-0000-0000-0000-000000000000",
            json={"name": "x", "version": 1},
        )
        assert resp.status_code == 404
