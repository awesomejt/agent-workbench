"""API contract tests for the ai_servers module."""

from __future__ import annotations


def _create(client, name="homelab-ollama", url="http://192.168.1.10:11434", server_type="ollama"):
    return client.post(
        "/api/ai-servers",
        json={"name": name, "url": url, "server_type": server_type},
    )


class TestCreateAiServer:
    def test_creates_with_required_fields(self, client):
        resp = _create(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "homelab-ollama"
        assert data["url"] == "http://192.168.1.10:11434"
        assert data["server_type"] == "ollama"
        assert data["status"] == "unknown"
        assert data["last_checked_at"] is None
        assert data["last_up_at"] is None

    def test_all_valid_server_types_accepted(self, client):
        for i, st in enumerate(["ollama", "litellm", "omlx", "openai_compat"]):
            resp = _create(client, name=f"srv-{i}", url=f"http://host-{i}:8080", server_type=st)
            assert resp.status_code == 201, f"Expected 201 for server_type={st}"

    def test_invalid_server_type_rejected(self, client):
        resp = _create(client, server_type="huggingface")
        assert resp.status_code == 422

    def test_missing_required_fields_rejected(self, client):
        resp = client.post("/api/ai-servers", json={"name": "x"})
        assert resp.status_code == 422

    def test_duplicate_name_rejected(self, client):
        _create(client)
        resp = _create(client)
        assert resp.status_code == 409

    def test_optional_notes_stored(self, client):
        resp = client.post(
            "/api/ai-servers",
            json={"name": "s", "url": "http://x:11434", "server_type": "ollama", "notes": "hi"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["notes"] == "hi"


class TestListAiServers:
    def test_empty_list(self, client):
        resp = client.get("/api/ai-servers")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_lists_created_servers(self, client):
        _create(client, name="a", url="http://a:1")
        _create(client, name="b", url="http://b:1")
        resp = client.get("/api/ai-servers")
        assert resp.get_json()["total"] == 2

    def test_filter_by_status(self, client):
        resp_a = _create(client, name="a", url="http://a:1").get_json()
        _create(client, name="b", url="http://b:1")
        # Set a to "up"
        client.patch(
            f"/api/ai-servers/{resp_a['id']}",
            json={"status": "up", "version": resp_a["version"]},
        )
        resp = client.get("/api/ai-servers?status=up")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "a"

    def test_available_filter(self, client):
        resp_a = _create(client, name="a", url="http://a:1").get_json()
        _create(client, name="b", url="http://b:1")
        client.patch(
            f"/api/ai-servers/{resp_a['id']}",
            json={"status": "up", "version": resp_a["version"]},
        )
        resp = client.get("/api/ai-servers?available=true")
        assert resp.get_json()["total"] == 1

    def test_invalid_status_filter_rejected(self, client):
        resp = client.get("/api/ai-servers?status=broken")
        assert resp.status_code == 422


class TestGetAiServer:
    def test_returns_server(self, client):
        sid = _create(client).get_json()["id"]
        resp = client.get(f"/api/ai-servers/{sid}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == sid

    def test_404_for_unknown(self, client):
        resp = client.get("/api/ai-servers/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_400_for_invalid_uuid(self, client):
        resp = client.get("/api/ai-servers/not-a-uuid")
        assert resp.status_code == 400


class TestUpdateAiServer:
    def test_updates_status_and_sets_timestamps(self, client):
        server = _create(client).get_json()
        resp = client.patch(
            f"/api/ai-servers/{server['id']}",
            json={"status": "up", "version": server["version"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "up"
        assert data["last_checked_at"] is not None
        assert data["last_up_at"] is not None
        assert data["version"] == 2

    def test_down_status_sets_last_checked_but_not_last_up(self, client):
        server = _create(client).get_json()
        resp = client.patch(
            f"/api/ai-servers/{server['id']}",
            json={"status": "down", "last_error": "connection refused", "version": 1},
        )
        data = resp.get_json()
        assert data["status"] == "down"
        assert data["last_checked_at"] is not None
        assert data["last_up_at"] is None
        assert data["last_error"] == "connection refused"

    def test_updates_url_and_notes(self, client):
        server = _create(client).get_json()
        resp = client.patch(
            f"/api/ai-servers/{server['id']}",
            json={"url": "http://new-host:11434", "notes": "moved", "version": 1},
        )
        data = resp.get_json()
        assert data["url"] == "http://new-host:11434"
        assert data["notes"] == "moved"

    def test_requires_version(self, client):
        sid = _create(client).get_json()["id"]
        resp = client.patch(f"/api/ai-servers/{sid}", json={"status": "up"})
        assert resp.status_code == 422

    def test_version_conflict(self, client):
        server = _create(client).get_json()
        resp = client.patch(
            f"/api/ai-servers/{server['id']}",
            json={"status": "up", "version": 99},
        )
        assert resp.status_code == 409

    def test_invalid_status_rejected(self, client):
        server = _create(client).get_json()
        resp = client.patch(
            f"/api/ai-servers/{server['id']}",
            json={"status": "degraded", "version": 1},
        )
        assert resp.status_code == 422


class TestDeleteAiServer:
    def test_deletes_server(self, client):
        sid = _create(client).get_json()["id"]
        resp = client.delete(f"/api/ai-servers/{sid}")
        assert resp.status_code == 204
        assert client.get(f"/api/ai-servers/{sid}").status_code == 404

    def test_404_for_unknown(self, client):
        resp = client.delete("/api/ai-servers/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
