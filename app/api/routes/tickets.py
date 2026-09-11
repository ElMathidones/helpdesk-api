from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    service = TicketService(db)

    try:
        return service.create_ticket(
            data=data,
            creator_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[TicketResponse],
)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketResponse]:
    service = TicketService(db)

    if current_user.role == UserRole.CUSTOMER:
        return service.list_tickets_by_creator(current_user.id)

    return service.list_all_tickets()


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    service = TicketService(db)

    try:
        return service.get_ticket(
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


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.TECHNICIAN,
        )
    ),
) -> TicketResponse:
    service = TicketService(db)

    try:
        return service.assign_ticket(
            ticket_id=ticket_id,
            assignee_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
