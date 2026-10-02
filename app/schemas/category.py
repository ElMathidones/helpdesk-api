from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class CategoryOrderUpdate(BaseModel):
    category_ids: list[int] = Field(min_length=1)


class CategoryStatusUpdate(BaseModel):
    is_active: bool
