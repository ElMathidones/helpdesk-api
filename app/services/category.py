from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryOrderUpdate,
    CategoryStatusUpdate,
    CategoryUpdate,
)


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
            sort_order=self.repository.get_next_sort_order(),
        )

    def update_category(
        self,
        category_id: int,
        data: CategoryUpdate,
    ) -> Category:
        category = self.repository.get_by_id(category_id)

        if category is None:
            raise LookupError("Category not found")

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing_category = self.repository.get_by_name(update_data["name"])

            if existing_category is not None and existing_category.id != category_id:
                raise ValueError("Category already exists")

        return self.repository.update(
            category,
            data=update_data,
        )

    def list_categories(self) -> list[Category]:
        return self.repository.list_all()

    def reorder_categories(
        self,
        data: CategoryOrderUpdate,
    ) -> list[Category]:
        categories = self.repository.list_all()

        current_ids = {category.id for category in categories}

        requested_ids = data.category_ids

        if len(requested_ids) != len(set(requested_ids)):
            raise ValueError("Category order contains duplicate ids")

        if set(requested_ids) != current_ids:
            raise ValueError("Category order must include all categories")

        return self.repository.reorder(requested_ids)

    def update_category_status(
        self,
        category_id: int,
        data: CategoryStatusUpdate,
    ) -> Category:
        category = self.repository.get_by_id(category_id)

        if category is None:
            raise LookupError("Category not found")

        return self.repository.update_status(
            category,
            is_active=data.is_active,
        )
