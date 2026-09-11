from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    CUSTOMER = "customer"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELED = "canceled"
