from app.services.email import EmailDeliveryError, EmailService


def create_authenticated_user(client):
    response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "original@example.com",
            "password": "senha123",
        },
    )

    assert response.status_code == 201

    login = client.post(
        "/auth/login",
        data={
            "username": "original@example.com",
            "password": "senha123",
        },
    )

    assert login.status_code == 200

    return {"Authorization": (f"Bearer {login.json()['access_token']}")}


def test_request_and_confirm_email_change(
    client,
    monkeypatch,
):
    headers = create_authenticated_user(client)
    sent = {}

    def fake_send(
        self,
        *,
        recipient_email,
        recipient_name,
        token,
    ):
        sent["email"] = recipient_email
        sent["token"] = token

    monkeypatch.setattr(
        EmailService,
        "send_email_change_confirmation",
        fake_send,
    )

    response = client.patch(
        "/users/me/email",
        headers=headers,
        json={
            "email": "novo@example.com",
            "current_password": "senha123",
        },
    )

    assert response.status_code == 202
    assert response.json() == {"message": "Confirmation email sent"}

    assert sent["email"] == "novo@example.com"

    before = client.get("/users/me", headers=headers)

    assert before.json()["email"] == "original@example.com"

    confirmation = client.post(
        "/users/confirm-email",
        json={"token": sent["token"]},
    )

    assert confirmation.status_code == 200

    after = client.get("/users/me", headers=headers)

    assert after.json()["email"] == "novo@example.com"

    repeated = client.post(
        "/users/confirm-email",
        json={"token": sent["token"]},
    )

    assert repeated.status_code == 400


def test_email_change_delivery_failure(
    client,
    db,
    monkeypatch,
):
    headers = create_authenticated_user(client)

    def fake_send(
        self,
        *,
        recipient_email,
        recipient_name,
        token,
    ):
        raise EmailDeliveryError("Test delivery failure")

    monkeypatch.setattr(
        EmailService,
        "send_email_change_confirmation",
        fake_send,
    )

    response = client.patch(
        "/users/me/email",
        headers=headers,
        json={
            "email": "novo@example.com",
            "current_password": "senha123",
        },
    )

    assert response.status_code == 503

    from app.models.user import User

    user = db.query(User).filter(User.email == "original@example.com").first()

    assert user is not None

    db.refresh(user)

    assert user.pending_email is None
    assert user.email_change_token_hash is None
    assert user.email == "original@example.com"


def test_email_change_cooldown(
    client,
    monkeypatch,
):
    headers = create_authenticated_user(client)

    def fake_send(
        self,
        *,
        recipient_email,
        recipient_name,
        token,
    ):
        return None

    monkeypatch.setattr(
        EmailService,
        "send_email_change_confirmation",
        fake_send,
    )

    first = client.patch(
        "/users/me/email",
        headers=headers,
        json={
            "email": "primeiro@example.com",
            "current_password": "senha123",
        },
    )

    second = client.patch(
        "/users/me/email",
        headers=headers,
        json={
            "email": "segundo@example.com",
            "current_password": "senha123",
        },
    )

    assert first.status_code == 202
    assert second.status_code == 429


def test_email_change_requires_authentication(client):
    response = client.patch(
        "/users/me/email",
        json={
            "email": "novo@example.com",
            "current_password": "senha123",
        },
    )

    assert response.status_code == 401


def test_invalid_confirmation_token(client):
    response = client.post(
        "/users/confirm-email",
        json={"token": "token-invalido"},
    )

    assert response.status_code == 400
