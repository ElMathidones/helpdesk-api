from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.category import CategoryService

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> CategoryResponse:
    service = CategoryService(db)

    try:
        return service.create_category(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    service = CategoryService(db)
    return service.list_categories()
