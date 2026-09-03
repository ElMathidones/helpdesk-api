from fastapi.testclient import TestClient


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
