import logging
from html import escape
from urllib.parse import quote

import resend

from app.core.config import get_settings

logger = logging.getLogger(__name__)

PRIORITY_LABELS = {
    "low": "Baixa",
    "medium": "Média",
    "high": "Alta",
    "critical": "Crítica",
}


class EmailDeliveryError(Exception):
    pass


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_ticket_created_copy(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        ticket_number: int,
        title: str,
        description: str,
        priority: str,
        category_name: str,
    ) -> None:
        if not self.settings.resend_api_key:
            logger.warning("Ticket email copy skipped because Resend is not configured")
            return

        resend.api_key = self.settings.resend_api_key

        priority_label = PRIORITY_LABELS.get(priority, priority)

        html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Chamado #{ticket_number} criado com sucesso</h2>

            <p>
                Olá, <strong>{escape(recipient_name)}</strong>.
            </p>

            <p>
                Recebemos sua solicitação no Help Desk.
            </p>

            <p>
                <strong>Título:</strong> {escape(title)}<br>
                <strong>Categoria:</strong> {escape(category_name)}<br>
                <strong>Prioridade:</strong> {escape(priority_label)}<br>
                <strong>Status:</strong> Aberto
            </p>

            <p><strong>Descrição:</strong></p>

            <p style="white-space: pre-wrap;">
                {escape(description)}
            </p>
        </div>
        """

        try:
            resend.Emails.send(
                {
                    "from": self.settings.email_from,
                    "to": [recipient_email],
                    "subject": f"Chamado #{ticket_number} criado com sucesso",
                    "html": html,
                }
            )
        except Exception:
            logger.exception(
                "Failed to send ticket email copy for ticket %s",
                ticket_number,
            )

    def send_ticket_assigned_notification(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        ticket_id: int,
        title: str,
        priority: str,
        category_name: str,
        customer_name: str,
    ) -> None:
        if not self.settings.resend_api_key:
            logger.warning(
                "Ticket assignment email skipped because Resend is not configured"
            )
            return

        resend.api_key = self.settings.resend_api_key

        priority_label = PRIORITY_LABELS.get(priority, priority)

        html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Chamado #{ticket_id} atribuído a você</h2>

            <p>
                Olá, <strong>{escape(recipient_name)}</strong>.
            </p>

            <p>
                Você assumiu um chamado no Help Desk e agora é o responsável
                pelo atendimento.
            </p>

            <p>
                <strong>Título:</strong> {escape(title)}<br>
                <strong>Cliente:</strong> {escape(customer_name)}<br>
                <strong>Categoria:</strong> {escape(category_name)}<br>
                <strong>Prioridade:</strong> {escape(priority_label)}<br>
                <strong>Status:</strong> Em andamento
            </p>
        </div>
        """

        try:
            resend.Emails.send(
                {
                    "from": self.settings.email_from,
                    "to": [recipient_email],
                    "subject": f"Chamado #{ticket_id} atribuído a você",
                    "html": html,
                }
            )
        except Exception:
            logger.exception(
                "Failed to send ticket assignment email for ticket %s",
                ticket_id,
            )

    def send_email_change_confirmation(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        token: str,
    ) -> None:
        if not self.settings.resend_api_key:
            raise EmailDeliveryError("Email service is not configured")

        resend.api_key = self.settings.resend_api_key

        confirmation_url = (
            f"{self.settings.frontend_url.rstrip('/')}"
            f"/confirm-email?token={quote(token, safe='')}"
        )

        safe_name = escape(recipient_name)
        safe_url = escape(confirmation_url, quote=True)

        expires_minutes = self.settings.email_change_token_expire_minutes

        html = f"""
        <div style="
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 560px;
            margin: 0 auto;
            color: #1f2937;
        ">
            <h2>Confirme seu novo e-mail</h2>

            <p>Olá, <strong>{safe_name}</strong>.</p>

            <p>
                Recebemos uma solicitação para alterar
                o endereço de e-mail da sua conta Helpdesk.
            </p>

            <p>
                Para confirmar a alteração,
                clique no botão abaixo:
            </p>

            <p style="margin: 28px 0;">
                <a
                    href="{safe_url}"
                    style="
                        display: inline-block;
                        padding: 12px 20px;
                        border-radius: 8px;
                        background: #4f46e5;
                        color: #ffffff;
                        text-decoration: none;
                        font-weight: 600;
                    "
                >
                    Confirmar novo e-mail
                </a>
            </p>

            <p>
                Este link é válido por
                <strong>{expires_minutes} minutos</strong>
                e só pode ser utilizado uma vez.
            </p>

            <p>
                Se você não solicitou esta alteração,
                ignore esta mensagem.
                Seu endereço atual permanecerá válido.
            </p>

            <hr style="
                border: 0;
                border-top: 1px solid #e5e7eb;
                margin: 24px 0;
            ">

            <p style="font-size: 12px; color: #6b7280;">
                Se o botão não funcionar,
                copie este endereço no navegador:
            </p>

            <p style="
                font-size: 12px;
                overflow-wrap: anywhere;
            ">
                {safe_url}
            </p>
        </div>
        """

        try:
            resend.Emails.send(
                {
                    "from": self.settings.email_from,
                    "to": [recipient_email],
                    "subject": "Confirme a alteração de e-mail - Helpdesk",
                    "html": html,
                }
            )
        except Exception as exc:
            logger.error("Failed to send email change confirmation")

            raise EmailDeliveryError("Unable to send confirmation email") from exc
