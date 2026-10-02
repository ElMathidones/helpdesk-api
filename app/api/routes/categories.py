from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryOrderUpdate,
    CategoryResponse,
    CategoryStatusUpdate,
    CategoryUpdate,
)
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


@router.put(
    "/order",
    response_model=list[CategoryResponse],
)
def reorder_categories(
    data: CategoryOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[CategoryResponse]:
    service = CategoryService(db)

    try:
        return service.reorder_categories(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> CategoryResponse:
    service = CategoryService(db)

    try:
        return service.update_category(category_id, data)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{category_id}/status",
    response_model=CategoryResponse,
)
def update_category_status(
    category_id: int,
    data: CategoryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> CategoryResponse:
    service = CategoryService(db)

    try:
        return service.update_category_status(
            category_id,
            data,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
