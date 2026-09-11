from sqlalchemy.orm import Session

from app.models.ticket import Ticket
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
