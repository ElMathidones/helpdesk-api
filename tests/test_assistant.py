from app.api.routes.assistant import assistant_rate_limiter


def login_user(client, email: str, password: str = "senha123") -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_assistant_rate_limit_blocks_after_ten_requests(
    client,
    monkeypatch,
):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Assistente",
            "email": "assistente@example.com",
            "password": "senha123",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]
    token = login_user(
        client,
        "assistente@example.com",
    )

    def fake_answer_question(
        self,
        *,
        message: str,
        user_role: str,
    ) -> str:
        return "Resposta simulada."

    monkeypatch.setattr(
        "app.api.routes.assistant.AssistantService.answer_question",
        fake_answer_question,
    )

    limiter_key = str(user_id)
    assistant_rate_limiter.reset(limiter_key)

    try:
        for _ in range(10):
            response = client.post(
                "/assistant/chat",
                json={
                    "message": "Como funciona o Help Desk?",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

            assert response.status_code == 200
            assert response.json() == {"answer": "Resposta simulada."}

        blocked_response = client.post(
            "/assistant/chat",
            json={
                "message": "Mais uma pergunta",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert blocked_response.status_code == 429

        assert blocked_response.json() == {
            "detail": ("Too many assistant requests. " "Try again later.")
        }

        assert "Retry-After" in blocked_response.headers

        retry_after = int(blocked_response.headers["Retry-After"])

        assert 1 <= retry_after <= 60

    finally:
        assistant_rate_limiter.reset(limiter_key)
