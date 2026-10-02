from sqlalchemy.orm import Session

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.ticket import TicketRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_history import TicketHistoryService


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.ticket_repository = TicketRepository(db)
        self.category_repository = CategoryRepository(db)
        self.history_service = TicketHistoryService(db)

    def create_ticket(
        self,
        data: TicketCreate,
        creator_id: int,
    ) -> Ticket:
        category = self.category_repository.get_by_id(data.category_id)

        if category is None or not category.is_active:
            raise ValueError("Category not found")

        if not category.is_active:
            raise ValueError("Category is inactive")

        ticket = self.ticket_repository.create(
            title=data.title,
            description=data.description,
            priority=data.priority,
            category_id=data.category_id,
            creator_id=creator_id,
        )

        self.history_service.create_event(
            ticket_id=ticket.id,
            user_id=creator_id,
            event_type="ticket_created",
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

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

        old_status = ticket.status

        ticket = self.ticket_repository.assign(
            ticket=ticket,
            assignee_id=assignee_id,
        )

        self.history_service.create_event(
            ticket_id=ticket.id,
            user_id=assignee_id,
            event_type="assignee_changed",
            old_value=None,
            new_value=str(assignee_id),
        )

        if old_status != ticket.status:
            self.history_service.create_event(
                ticket_id=ticket.id,
                user_id=assignee_id,
                event_type="status_changed",
                old_value=old_status.value,
                new_value=ticket.status.value,
            )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def update_ticket_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        current_user: User,
    ) -> Ticket:
        ticket = self.ticket_repository.get_by_id(ticket_id)

        if ticket is None:
            raise ValueError("Ticket not found")

        allowed_transitions = {
            TicketStatus.OPEN: {
                TicketStatus.UNDER_REVIEW,
                TicketStatus.IN_PROGRESS,
                TicketStatus.CANCELED,
            },
            TicketStatus.UNDER_REVIEW: {
                TicketStatus.IN_PROGRESS,
                TicketStatus.CANCELED,
            },
            TicketStatus.IN_PROGRESS: {
                TicketStatus.RESOLVED,
                TicketStatus.CANCELED,
            },
            TicketStatus.RESOLVED: {
                TicketStatus.IN_PROGRESS,
                TicketStatus.CLOSED,
            },
            TicketStatus.CLOSED: set(),
            TicketStatus.CANCELED: set(),
        }

        if new_status not in allowed_transitions[ticket.status]:
            raise ValueError(
                f"Cannot change ticket status from "
                f"{ticket.status.value} to {new_status.value}"
            )

        old_status = ticket.status

        ticket = self.ticket_repository.update_status(
            ticket=ticket,
            new_status=new_status,
        )

        self.history_service.create_event(
            ticket_id=ticket.id,
            user_id=current_user.id,
            event_type="status_changed",
            old_value=old_status.value,
            new_value=new_status.value,
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket
