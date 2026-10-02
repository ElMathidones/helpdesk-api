from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def login_user(
    client: TestClient,
    email: str,
    password: str = "senha123",
) -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_test_user(
    client: TestClient,
    *,
    name: str = "Mathias",
    email: str = "mathias@example.com",
) -> None:
    response = client.post(
        "/users",
        json={
            "name": name,
            "email": email,
            "password": "senha123",
        },
    )

    assert response.status_code == 201


def test_create_user(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={
            "name": "Mathias",
            "email": "mathias@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Mathias"
    assert data["email"] == "mathias@example.com"
    assert data["role"] == "customer"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_with_duplicate_email(client: TestClient) -> None:
    payload = {
        "name": "Mathias",
        "email": "mathias@example.com",
        "password": "senha123",
    }

    first_response = client.post("/users", json=payload)
    second_response = client.post("/users", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email already registered",
    }


def test_authenticated_user_can_update_own_name(
    client: TestClient,
) -> None:
    create_test_user(client)

    token = login_user(client, "mathias@example.com")

    response = client.patch(
        "/users/me",
        json={
            "name": "Mathias Atualizado",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Mathias Atualizado"

    me_response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["name"] == "Mathias Atualizado"


def test_update_current_user_requires_authentication(
    client: TestClient,
) -> None:
    response = client.patch(
        "/users/me",
        json={
            "name": "Novo nome",
        },
    )

    assert response.status_code == 401


def test_authenticated_user_can_upload_and_remove_avatar(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_test_user(client)

    token = login_user(client, "mathias@example.com")

    monkeypatch.setattr(
        "app.services.user.AVATAR_DIRECTORY",
        tmp_path,
    )

    upload_response = client.post(
        "/users/me/avatar",
        files={
            "avatar": (
                "avatar.png",
                b"\x89PNG\r\n\x1a\nfake-image-content",
                "image/png",
            ),
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert upload_response.status_code == 200

    avatar_filename = upload_response.json()["avatar_filename"]

    assert avatar_filename is not None
    assert avatar_filename.endswith(".png")
    assert (tmp_path / avatar_filename).is_file()

    remove_response = client.delete(
        "/users/me/avatar",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert remove_response.status_code == 200
    assert remove_response.json()["avatar_filename"] is None
    assert not (tmp_path / avatar_filename).exists()


def test_avatar_rejects_invalid_content_type(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_test_user(client)

    token = login_user(client, "mathias@example.com")

    monkeypatch.setattr(
        "app.services.user.AVATAR_DIRECTORY",
        tmp_path,
    )

    response = client.post(
        "/users/me/avatar",
        files={
            "avatar": (
                "avatar.txt",
                b"not-an-image",
                "text/plain",
            ),
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Avatar must be a JPEG, PNG or WebP image",
    }

    assert list(tmp_path.iterdir()) == []


def test_avatar_rejects_file_larger_than_2_mb(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_test_user(client)

    token = login_user(client, "mathias@example.com")

    monkeypatch.setattr(
        "app.services.user.AVATAR_DIRECTORY",
        tmp_path,
    )

    response = client.post(
        "/users/me/avatar",
        files={
            "avatar": (
                "avatar.png",
                b"x" * (2 * 1024 * 1024 + 1),
                "image/png",
            ),
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Avatar must not exceed 2 MB",
    }

    assert list(tmp_path.iterdir()) == []
