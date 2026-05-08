import pytest
from fastapi.testclient import TestClient
from tests.conftest import create_test_user, auth_headers


def setup_user_and_project(client: TestClient, email="owner@example.com"):
    create_test_user(client, email=email, full_name="Owner")
    headers = auth_headers(client, email=email)
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Test Project", "description": "A test"},
        headers=headers,
    )
    assert resp.status_code == 201
    return headers, resp.json()


class TestProjectCRUD:
    def test_create_project(self, client: TestClient):
        create_test_user(client)
        headers = auth_headers(client)
        resp = client.post(
            "/api/v1/projects/",
            json={"name": "My Project", "description": "Desc"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Project"
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "owner"

    def test_list_projects(self, client: TestClient):
        create_test_user(client)
        headers = auth_headers(client)
        client.post("/api/v1/projects/", json={"name": "P1"}, headers=headers)
        client.post("/api/v1/projects/", json={"name": "P2"}, headers=headers)
        resp = client.get("/api/v1/projects/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_project_detail(self, client: TestClient):
        headers, project = setup_user_and_project(client)
        resp = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == project["id"]

    def test_update_project(self, client: TestClient):
        headers, project = setup_user_and_project(client)
        resp = client.patch(
            f"/api/v1/projects/{project['id']}",
            json={"name": "Renamed"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

    def test_delete_project(self, client: TestClient):
        headers, project = setup_user_and_project(client)
        resp = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
        assert resp.status_code == 404

    def test_non_member_cannot_see_project(self, client: TestClient):
        _, project = setup_user_and_project(client)
        create_test_user(client, email="stranger@example.com")
        stranger_headers = auth_headers(client, email="stranger@example.com")
        resp = client.get(f"/api/v1/projects/{project['id']}", headers=stranger_headers)
        assert resp.status_code == 403


class TestProjectMembers:
    def test_add_member(self, client: TestClient):
        headers, project = setup_user_and_project(client)
        # Create a second user
        create_test_user(client, email="member@example.com", full_name="Member")
        member_login = client.post(
            "/api/v1/auth/login",
            json={"email": "member@example.com", "password": "testpass123"},
        ).json()
        member_id = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {member_login['access_token']}"},
        ).json()["id"]

        resp = client.post(
            f"/api/v1/projects/{project['id']}/members",
            json={"user_id": member_id, "role": "editor"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "editor"

    def test_non_owner_cannot_add_member(self, client: TestClient):
        _, project = setup_user_and_project(client)
        create_test_user(client, email="rando@example.com")
        rando_headers = auth_headers(client, email="rando@example.com")
        resp = client.post(
            f"/api/v1/projects/{project['id']}/members",
            json={"user_id": 999, "role": "viewer"},
            headers=rando_headers,
        )
        assert resp.status_code == 403
