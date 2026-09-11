from app.models.user import User


def test_login_with_valid_credentials(client):
    client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "usuario@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_password(client):
    client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "usuario@example.com",
            "password": "senha_errada",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_login_with_unknown_email(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "naoexiste@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_inactive_user_cannot_login(client, db):
    client.post(
        "/users",
        json={
            "name": "Usuário Inativo",
            "email": "inativo@example.com",
            "password": "senha123",
        },
    )

    user = db.query(User).filter(User.email == "inativo@example.com").first()

    assert user is not None

    user.is_active = False
    db.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "inativo@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Inactive user"}


def test_protected_route_without_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
