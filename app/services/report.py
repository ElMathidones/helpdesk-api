from datetime import date

from sqlalchemy.orm import Session

from app.repositories.report import ReportRepository


class ReportService:
    def __init__(self, db: Session) -> None:
        self.repository = ReportRepository(db)

    @staticmethod
    def _validate_date_range(
        start_date: date | None,
        end_date: date | None,
    ) -> None:
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("A data inicial não pode ser posterior à data final.")

    def get_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, int]:
        self._validate_date_range(start_date, end_date)

        return self.repository.get_summary(
            start_date=start_date,
            end_date=end_date,
        )

    def get_timeline(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        self._validate_date_range(start_date, end_date)

        return self.repository.get_timeline(
            start_date=start_date,
            end_date=end_date,
        )

    def get_priority_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        self._validate_date_range(start_date, end_date)

        return self.repository.get_priority_distribution(
            start_date=start_date,
            end_date=end_date,
        )

    def get_category_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        self._validate_date_range(start_date, end_date)

        return self.repository.get_category_distribution(
            start_date=start_date,
            end_date=end_date,
        )

    def get_status_distribution(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        self._validate_date_range(start_date, end_date)

        return self.repository.get_status_distribution(
            start_date=start_date,
            end_date=end_date,
        )
