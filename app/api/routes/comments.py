from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment import CommentService
from app.services.websocket import manager

router = APIRouter(prefix="/tickets", tags=["comments"])


@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    ticket_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentResponse:
    service = CommentService(db)

    try:
        comment = service.create_comment(
            ticket_id=ticket_id,
            author_id=current_user.id,
            data=data,
        )

        await manager.broadcast(
            ticket_id=ticket_id,
            message={
                "type": "comment_created",
                "comment": comment.model_dump(mode="json"),
            },
        )

        return comment
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/{ticket_id}/comments",
    response_model=list[CommentResponse],
)
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CommentResponse]:
    service = CommentService(db)

    try:
        return service.list_comments(
            ticket_id=ticket_id,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
