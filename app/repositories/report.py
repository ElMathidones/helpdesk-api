from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TicketStatus
from app.models.ticket import Ticket


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, int]:
        statement = select(
            func.count(Ticket.id).label("total"),
            func.count(Ticket.id)
            .filter(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.UNDER_REVIEW]))
            .label("open"),
            func.count(Ticket.id)
            .filter(Ticket.status == TicketStatus.IN_PROGRESS)
            .label("in_progress"),
            func.count(Ticket.id)
            .filter(Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))
            .label("resolved"),
            func.count(Ticket.id)
            .filter(Ticket.status == TicketStatus.CANCELED)
            .label("canceled"),
        )

        if start_date is not None:
            statement = statement.where(
                Ticket.created_at >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Ticket.created_at < end_date + timedelta(days=1),
            )

        result = self.db.execute(statement).one()

        return {
            "total": result.total,
            "open": result.open,
            "in_progress": result.in_progress,
            "resolved": result.resolved,
            "canceled": result.canceled,
        }

    def get_timeline(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        statement = (
            select(
                func.date(Ticket.created_at).label("date"),
                func.count(Ticket.id).label("created"),
            )
            .group_by(func.date(Ticket.created_at))
            .order_by(func.date(Ticket.created_at))
        )

        if start_date is not None:
            statement = statement.where(
                Ticket.created_at >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Ticket.created_at < end_date + timedelta(days=1),
            )

        results = self.db.execute(statement).all()

        return [
            {
                "date": row.date,
                "created": row.created,
            }
            for row in results
        ]

    def get_priority_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        statement = (
            select(
                Ticket.priority.label("priority"),
                func.count(Ticket.id).label("count"),
            )
            .group_by(Ticket.priority)
            .order_by(Ticket.priority)
        )

        if start_date is not None:
            statement = statement.where(
                Ticket.created_at >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Ticket.created_at < end_date + timedelta(days=1),
            )

        results = self.db.execute(statement).all()

        return [
            {
                "priority": row.priority.value,
                "count": row.count,
            }
            for row in results
        ]

    def get_category_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        statement = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.count(Ticket.id).label("count"),
            )
            .join(Ticket, Ticket.category_id == Category.id)
            .group_by(Category.id, Category.name)
            .order_by(Category.name)
        )

        if start_date is not None:
            statement = statement.where(
                Ticket.created_at >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Ticket.created_at < end_date + timedelta(days=1),
            )

        results = self.db.execute(statement).all()

        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "count": row.count,
            }
            for row in results
        ]

    def get_status_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        statement = (
            select(
                Ticket.status.label("status"),
                func.count(Ticket.id).label("count"),
            )
            .group_by(Ticket.status)
            .order_by(Ticket.status)
        )

        if start_date is not None:
            statement = statement.where(
                Ticket.created_at >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Ticket.created_at < end_date + timedelta(days=1),
            )

        results = self.db.execute(statement).all()

        return [
            {
                "status": row.status.value,
                "count": row.count,
            }
            for row in results
        ]
