from sqlalchemy import select
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
    ) -> Category:
        category = Category(
            name=name,
            description=description,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    def list_all(self) -> list[Category]:
        statement = select(Category).order_by(Category.name)
        return list(self.db.scalars(statement).all())
