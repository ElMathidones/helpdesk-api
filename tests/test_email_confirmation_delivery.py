from types import SimpleNamespace

import pytest
import resend

from app.services.email import EmailDeliveryError, EmailService


def make_email_service():
    service = EmailService()

    service.settings = SimpleNamespace(
        resend_api_key="test-api-key",
        email_from="Helpdesk <test@example.com>",
        frontend_url="http://localhost:5173",
        email_change_token_expire_minutes=30,
    )

    return service


def test_send_email_change_confirmation(monkeypatch):
    service = make_email_service()
    captured = {}

    def fake_send(payload):
        captured.update(payload)
        return {"id": "test-email-id"}

    monkeypatch.setattr(
        resend.Emails,
        "send",
        fake_send,
    )

    service.send_email_change_confirmation(
        recipient_email="novo@example.com",
        recipient_name="Usuário Teste",
        token="token-teste-123",
    )

    assert captured["to"] == ["novo@example.com"]
    assert "Confirme" in captured["subject"]

    assert ("http://localhost:5173/" "confirm-email?token=token-teste-123") in captured[
        "html"
    ]

    assert "30 minutos" in captured["html"]


def test_email_change_requires_resend_configuration():
    service = make_email_service()
    service.settings.resend_api_key = None

    with pytest.raises(EmailDeliveryError):
        service.send_email_change_confirmation(
            recipient_email="novo@example.com",
            recipient_name="Usuário Teste",
            token="token-teste-123",
        )


def test_email_change_handles_resend_failure(monkeypatch):
    service = make_email_service()

    def fake_send(_payload):
        raise RuntimeError("Resend unavailable")

    monkeypatch.setattr(
        resend.Emails,
        "send",
        fake_send,
    )

    with pytest.raises(EmailDeliveryError):
        service.send_email_change_confirmation(
            recipient_email="novo@example.com",
            recipient_name="Usuário Teste",
            token="token-teste-123",
        )
