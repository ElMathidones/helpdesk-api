from sqlalchemy.orm import Session

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.ticket import TicketRepository
from app.schemas.ticket import TicketCreate


class TicketService:
    def __init__(self, db: Session) -> None:
        self.ticket_repository = TicketRepository(db)
        self.category_repository = CategoryRepository(db)

    def create_ticket(
        self,
        data: TicketCreate,
        creator_id: int,
    ) -> Ticket:
        category = self.category_repository.get_by_id(data.category_id)

        if category is None:
            raise ValueError("Category not found")

        if not category.is_active:
            raise ValueError("Category is inactive")

        return self.ticket_repository.create(
            title=data.title,
            description=data.description,
            priority=data.priority,
            category_id=data.category_id,
            creator_id=creator_id,
        )

    def list_all_tickets(self) -> list[Ticket]:
        return self.ticket_repository.list_all()

    def list_tickets_by_creator(
        self,
        creator_id: int,
    ) -> list[Ticket]:
        return self.ticket_repository.list_by_creator(creator_id)

    def get_ticket(
        self,
        ticket_id: int,
        current_user: User,
    ) -> Ticket:
        ticket = self.ticket_repository.get_by_id(ticket_id)

        if ticket is None:
            raise ValueError("Ticket not found")

        if (
            current_user.role == UserRole.CUSTOMER
            and ticket.creator_id != current_user.id
        ):
            raise PermissionError("Insufficient permissions")

        return ticket

    def assign_ticket(
        self,
        ticket_id: int,
        assignee_id: int,
    ) -> Ticket:
        ticket = self.ticket_repository.get_by_id(ticket_id)

        if ticket is None:
            raise ValueError("Ticket not found")

        if ticket.assignee_id is not None:
            raise ValueError("Ticket is already assigned")

        if ticket.status in {
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
            TicketStatus.CANCELED,
        }:
            raise ValueError("Ticket cannot be assigned in its current status")

        return self.ticket_repository.assign(
            ticket=ticket,
            assignee_id=assignee_id,
        )
