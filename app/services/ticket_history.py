from sqlalchemy.orm import Session

from app.models.ticket_history import TicketHistory
from app.repositories.ticket_history import TicketHistoryRepository


class TicketHistoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketHistoryRepository(db)

    def create_event(
        self,
        *,
        ticket_id: int,
        user_id: int | None,
        event_type: str,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> TicketHistory:
        return self.repository.create(
            ticket_id=ticket_id,
            user_id=user_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
        )

    def list_by_ticket(self, ticket_id: int) -> list[TicketHistory]:
        return self.repository.list_by_ticket(ticket_id)
