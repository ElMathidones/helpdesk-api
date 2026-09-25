from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment


def create_comment(
    db: Session,
    ticket_id: int,
    author_id: int,
    content: str,
) -> Comment:
    comment = Comment(
        ticket_id=ticket_id,
        author_id=author_id,
        content=content,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def get_comments_by_ticket(
    db: Session,
    ticket_id: int,
) -> list[Comment]:
    statement = (
        select(Comment)
        .where(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
    )

    return list(db.scalars(statement).all())
