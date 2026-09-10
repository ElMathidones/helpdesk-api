from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.repository = CategoryRepository(db)

    def create_category(self, data: CategoryCreate) -> Category:
        existing_category = self.repository.get_by_name(data.name)

        if existing_category is not None:
            raise ValueError("Category already exists")

        return self.repository.create(
            name=data.name,
            description=data.description,
        )

    def list_categories(self) -> list[Category]:
        return self.repository.list_all()
