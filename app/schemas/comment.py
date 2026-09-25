from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    content: str


class CommentAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: int
    author: CommentAuthor
    content: str
    created_at: datetime
