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


def test_login_rate_limit_blocks_after_five_failed_attempts(client):
    client.post(
        "/users",
        json={
            "name": "Usuário Rate Limit",
            "email": "ratelimit@example.com",
            "password": "senha123",
        },
    )

    for _ in range(5):
        response = client.post(
            "/auth/login",
            data={
                "username": "ratelimit@example.com",
                "password": "senha_errada",
            },
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password"}

    blocked_response = client.post(
        "/auth/login",
        data={
            "username": "ratelimit@example.com",
            "password": "senha_errada",
        },
    )

    assert blocked_response.status_code == 429
    assert blocked_response.json() == {
        "detail": "Too many login attempts. Try again later."
    }

    assert "Retry-After" in blocked_response.headers

    retry_after = int(blocked_response.headers["Retry-After"])

    assert 1 <= retry_after <= 300


def test_successful_login_resets_failed_attempts(client):
    client.post(
        "/users",
        json={
            "name": "Usuário Reset",
            "email": "reset@example.com",
            "password": "senha123",
        },
    )

    for _ in range(4):
        response = client.post(
            "/auth/login",
            data={
                "username": "reset@example.com",
                "password": "senha_errada",
            },
        )

        assert response.status_code == 401

    successful_response = client.post(
        "/auth/login",
        data={
            "username": "reset@example.com",
            "password": "senha123",
        },
    )

    assert successful_response.status_code == 200

    for _ in range(5):
        response = client.post(
            "/auth/login",
            data={
                "username": "reset@example.com",
                "password": "senha_errada",
            },
        )

        assert response.status_code == 401
