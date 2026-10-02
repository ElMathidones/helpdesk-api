from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update(
        self,
        user: User,
        *,
        name: str,
    ) -> User:
        user.name = name

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_avatar(
        self,
        user: User,
        *,
        avatar_filename: str | None,
    ) -> User:
        user.avatar_filename = avatar_filename

        self.db.commit()
        self.db.refresh(user)

        return user
