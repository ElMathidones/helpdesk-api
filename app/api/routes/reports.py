from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import require_roles
from app.dependencies.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.report import (
    ReportCategoryItem,
    ReportPriorityItem,
    ReportStatusItem,
    ReportSummaryResponse,
    ReportTimelineItem,
)
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
)
def get_report_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)),
):
    service = ReportService(db)

    try:
        return service.get_summary(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/timeline",
    response_model=list[ReportTimelineItem],
)
def get_report_timeline(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)),
):
    service = ReportService(db)

    try:
        return service.get_timeline(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/by-priority",
    response_model=list[ReportPriorityItem],
)
def get_report_priority_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)),
):
    service = ReportService(db)

    try:
        return service.get_priority_distribution(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/by-category",
    response_model=list[ReportCategoryItem],
)
def get_report_category_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)),
):
    service = ReportService(db)

    try:
        return service.get_category_distribution(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/by-status",
    response_model=list[ReportStatusItem],
)
def get_report_status_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)),
):
    service = ReportService(db)

    try:
        return service.get_status_distribution(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
