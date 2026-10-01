from datetime import date

from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    canceled: int


class ReportTimelineItem(BaseModel):
    date: date
    created: int


class ReportPriorityItem(BaseModel):
    priority: str
    count: int


class ReportCategoryItem(BaseModel):
    category_id: int
    category_name: str
    count: int


class ReportStatusItem(BaseModel):
    status: str
    count: int
