from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.comments import create_comment, get_comments_by_ticket
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.ticket import TicketService


class CommentService:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_service = TicketService(db)

    def create_comment(
        self,
        ticket_id: int,
        author_id: int,
        data: CommentCreate,
    ) -> CommentResponse:
        author = self.db.get(User, author_id)

        if author is None:
            raise ValueError("User not found")

        self.ticket_service.get_ticket(
            ticket_id=ticket_id,
            current_user=author,
        )

        comment = create_comment(
            db=self.db,
            ticket_id=ticket_id,
            author_id=author_id,
            content=data.content,
        )

        return CommentResponse.model_validate(comment)

    def list_comments(
        self,
        ticket_id: int,
        current_user: User,
    ) -> list[CommentResponse]:
        self.ticket_service.get_ticket(
            ticket_id=ticket_id,
            current_user=current_user,
        )

        comments = get_comments_by_ticket(
            db=self.db,
            ticket_id=ticket_id,
        )

        return [CommentResponse.model_validate(comment) for comment in comments]
