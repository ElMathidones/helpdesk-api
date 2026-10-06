import logging
from html import escape

import resend

from app.core.config import get_settings

logger = logging.getLogger(__name__)

PRIORITY_LABELS = {
    "low": "Baixa",
    "medium": "Média",
    "high": "Alta",
    "critical": "Crítica",
}


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
