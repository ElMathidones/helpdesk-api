from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TicketPriority, TicketStatus
from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        title: str,
        description: str,
        priority: TicketPriority,
        category_id: int,
        creator_id: int,
    ) -> Ticket:
        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            category_id=category_id,
            creator_id=creator_id,
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def list_all(self) -> list[Ticket]:
        statement = select(Ticket).order_by(Ticket.created_at.desc())
        return list(self.db.scalars(statement).all())

    def list_by_creator(self, creator_id: int) -> list[Ticket]:
        statement = (
            select(Ticket)
            .where(Ticket.creator_id == creator_id)
            .order_by(Ticket.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def assign(
        self,
        ticket: Ticket,
        assignee_id: int,
    ) -> Ticket:
        ticket.assignee_id = assignee_id
        ticket.status = TicketStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def update_status(
        self,
        ticket: Ticket,
        new_status: TicketStatus,
    ) -> Ticket:
        ticket.status = new_status

        if new_status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(ticket)

        return ticket
