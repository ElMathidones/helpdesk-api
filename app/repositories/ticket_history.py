from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_history import TicketHistory


class TicketHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        ticket_id: int,
        user_id: int | None,
        event_type: str,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> TicketHistory:
        history = TicketHistory(
            ticket_id=ticket_id,
            user_id=user_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
        )

        self.db.add(history)
        self.db.flush()
        self.db.refresh(history)

        return history

    def list_by_ticket(self, ticket_id: int) -> list[TicketHistory]:
        statement = (
            select(TicketHistory)
            .where(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.created_at.asc())
        )

        return list(self.db.scalars(statement).all())
