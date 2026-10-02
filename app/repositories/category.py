from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, name: str) -> Category | None:
        statement = select(Category).where(Category.name == name)
        return self.db.scalar(statement)

    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def create(
        self,
        *,
        name: str,
        description: str | None,
        sort_order: int,
    ) -> Category:
        category = Category(
            name=name,
            description=description,
            sort_order=sort_order,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    def update(
        self,
        category: Category,
        *,
        data: dict[str, object],
    ) -> Category:
        for field, value in data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)

        return category

    def list_all(self) -> list[Category]:
        statement = select(Category).order_by(
            Category.sort_order,
            Category.id,
        )

        return list(self.db.scalars(statement).all())

    def get_next_sort_order(self) -> int:
        statement = select(func.coalesce(func.max(Category.sort_order), 0) + 1)

        return int(self.db.scalar(statement) or 1)

    def reorder(self, category_ids: list[int]) -> list[Category]:
        categories = self.list_all()
        categories_by_id = {category.id: category for category in categories}

        for position, category_id in enumerate(category_ids, start=1):
            categories_by_id[category_id].sort_order = position

        self.db.commit()

        return self.list_all()

    def update_status(
        self,
        category: Category,
        *,
        is_active: bool,
    ) -> Category:
        category.is_active = is_active

        self.db.commit()
        self.db.refresh(category)

        return category
