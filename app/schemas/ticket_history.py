from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketHistoryUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TicketHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    event_type: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
    user: TicketHistoryUserResponse | None
