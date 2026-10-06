from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.enums import TicketPriority, TicketStatus
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.user import User


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_next_creator_ticket_number(
        self,
        creator_id: int,
    ) -> int:
        user = self.db.scalar(
            select(User).where(User.id == creator_id).with_for_update()
        )

        if user is None:
            raise ValueError("Creator not found")

        ticket_number = user.next_ticket_number
        user.next_ticket_number += 1

        self.db.flush()

        return ticket_number

    def create(
        self,
        *,
        title: str,
        description: str,
        priority: TicketPriority,
        category_id: int,
        creator_id: int,
    ) -> Ticket:
        creator_ticket_number = self.get_next_creator_ticket_number(creator_id)

        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            category_id=category_id,
            creator_id=creator_id,
            creator_ticket_number=creator_ticket_number,
        )

        self.db.add(ticket)
        self.db.flush()
        self.db.refresh(ticket)

        return ticket

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def get_by_creator_ticket_number(
        self,
        creator_id: int,
        creator_ticket_number: int,
    ) -> Ticket | None:
        statement = select(Ticket).where(
            Ticket.creator_id == creator_id,
            Ticket.creator_ticket_number == creator_ticket_number,
        )

        return self.db.scalar(statement)

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

        self.db.flush()
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

    def delete(self, ticket: Ticket) -> None:
        self.db.execute(
            delete(Comment).where(
                Comment.ticket_id == ticket.id,
            )
        )

        self.db.execute(
            delete(TicketHistory).where(
                TicketHistory.ticket_id == ticket.id,
            )
        )

        self.db.delete(ticket)
        self.db.commit()
