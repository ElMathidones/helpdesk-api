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

        if category is None:
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

    def get_ticket_by_creator_number(
        self,
        creator_id: int,
        creator_ticket_number: int,
    ) -> Ticket:
        ticket = self.ticket_repository.get_by_creator_ticket_number(
            creator_id=creator_id,
            creator_ticket_number=creator_ticket_number,
        )

        if ticket is None:
            raise ValueError("Ticket not found")

        return ticket

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

        if ticket.status != TicketStatus.UNDER_REVIEW:
            raise ValueError("Ticket must be under review before assignment")

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
                TicketStatus.CANCELED,
            },
            TicketStatus.UNDER_REVIEW: {
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

        technician_can_start_analysis = (
            current_user.role == UserRole.TECHNICIAN
            and ticket.status == TicketStatus.OPEN
            and new_status == TicketStatus.UNDER_REVIEW
        )

        technician_owns_ticket = (
            current_user.role == UserRole.TECHNICIAN
            and ticket.assignee_id == current_user.id
        )

        if (
            current_user.role == UserRole.TECHNICIAN
            and not technician_can_start_analysis
            and not technician_owns_ticket
        ):
            raise PermissionError("Only the assigned technician can update this ticket")

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

    def release_ticket(
        self,
        ticket_id: int,
        current_user: User,
    ) -> Ticket:
        ticket = self.ticket_repository.get_by_id(ticket_id)

        if ticket is None:
            raise ValueError("Ticket not found")

        if ticket.status != TicketStatus.IN_PROGRESS:
            raise ValueError("Only tickets in progress can be released")

        if ticket.assignee_id is None:
            raise ValueError("Ticket is not assigned")

        if (
            current_user.role == UserRole.TECHNICIAN
            and ticket.assignee_id != current_user.id
        ):
            raise PermissionError(
                "Only the assigned technician can release this ticket"
            )

        old_assignee_id = ticket.assignee_id
        old_status = ticket.status

        ticket = self.ticket_repository.release(ticket)

        self.history_service.create_event(
            ticket_id=ticket.id,
            user_id=current_user.id,
            event_type="assignee_changed",
            old_value=str(old_assignee_id),
            new_value=None,
        )

        self.history_service.create_event(
            ticket_id=ticket.id,
            user_id=current_user.id,
            event_type="status_changed",
            old_value=old_status.value,
            new_value=ticket.status.value,
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def delete_ticket(
        self,
        ticket_id: int,
    ) -> None:
        ticket = self.ticket_repository.get_by_id(ticket_id)

        if ticket is None:
            raise LookupError("Ticket not found")

        self.ticket_repository.delete(ticket)
