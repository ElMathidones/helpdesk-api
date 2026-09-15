from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketPriority, TicketStatus


class TicketCategoryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class TicketUserResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM
    category_id: int = Field(gt=0)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus

    category_id: int
    creator_id: int
    assignee_id: int | None

    category: TicketCategoryResponse
    creator: TicketUserResponse
    assignee: TicketUserResponse | None

    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
