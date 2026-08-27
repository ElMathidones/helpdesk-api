from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    CUSTOMER = "customer"
