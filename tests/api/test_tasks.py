import pytest
from fastapi.testclient import TestClient
from tests.conftest import create_test_user, auth_headers


def setup_project_with_task(client: TestClient):
    create_test_user(client, email="owner@example.com", full_name="Owner")
    headers = auth_headers(client, email="owner@example.com")
    project = client.post(
        "/api/v1/projects/",
        json={"name": "Test Project"},
        headers=headers,
    ).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks/",
        json={"title": "First Task", "priority": "high"},
        headers=headers,
    ).json()
    return headers, project, task


class TestTaskCRUD:
    def test_create_task(self, client: TestClient):
        create_test_user(client)
        headers = auth_headers(client)
        project = client.post(
            "/api/v1/projects/", json={"name": "P"}, headers=headers
        ).json()
        resp = client.post(
            f"/api/v1/projects/{project['id']}/tasks/",
            json={"title": "Do something", "priority": "medium"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Do something"
        assert data["status"] == "todo"

    def test_list_tasks_with_filter(self, client: TestClient):
        headers, project, _ = setup_project_with_task(client)
        client.post(
            f"/api/v1/projects/{project['id']}/tasks/",
            json={"title": "Low prio task", "priority": "low"},
            headers=headers,
        )
        resp = client.get(
            f"/api/v1/projects/{project['id']}/tasks/?priority=high",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["priority"] == "high"

    def test_list_tasks_pagination(self, client: TestClient):
        create_test_user(client)
        headers = auth_headers(client)
        project = client.post("/api/v1/projects/", json={"name": "P"}, headers=headers).json()
        for i in range(5):
            client.post(
                f"/api/v1/projects/{project['id']}/tasks/",
                json={"title": f"Task {i}"},
                headers=headers,
            )
        resp = client.get(
            f"/api/v1/projects/{project['id']}/tasks/?page=1&size=3",
            headers=headers,
        )
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["pages"] == 2

    def test_update_task(self, client: TestClient):
        headers, project, task = setup_project_with_task(client)
        resp = client.patch(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}",
            json={"title": "Updated Title"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_update_task_status(self, client: TestClient):
        headers, project, task = setup_project_with_task(client)
        resp = client.patch(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}/status",
            json={"status": "in_progress"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_delete_task(self, client: TestClient):
        headers, project, task = setup_project_with_task(client)
        resp = client.delete(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}",
            headers=headers,
        )
        assert resp.status_code == 204
        resp = client.get(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_non_member_cannot_access_tasks(self, client: TestClient):
        _, project, task = setup_project_with_task(client)
        create_test_user(client, email="stranger@example.com")
        stranger_headers = auth_headers(client, email="stranger@example.com")
        resp = client.get(
            f"/api/v1/projects/{project['id']}/tasks/",
            headers=stranger_headers,
        )
        assert resp.status_code == 403
