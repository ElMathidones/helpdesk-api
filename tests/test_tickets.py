from app.models.enums import UserRole
from app.models.user import User


def test_admin_can_create_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    user = db.query(User).filter(User.email == "admin@example.com").first()

    assert user is not None

    user.role = UserRole.ADMIN
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "senha123",
        },
    )

    token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert category_response.status_code == 201

    data = category_response.json()

    assert data["name"] == "Hardware"
    assert data["is_active"] is True


def test_create_ticket(client):
    user_response = client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    assert user_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": "cliente@example.com",
            "password": "senha123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert category_response.status_code == 403
