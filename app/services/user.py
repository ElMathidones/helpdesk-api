from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(data.email)

        if existing_user is not None:
            raise ValueError("Email already registered")

        hashed_password = hash_password(data.password)

        return self.repository.create(
            name=data.name,
            email=data.email,
            password_hash=hashed_password,
        )
