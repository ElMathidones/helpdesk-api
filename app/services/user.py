from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

AVATAR_DIRECTORY = Path("uploads/avatars")

ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_AVATAR_SIZE = 2 * 1024 * 1024


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

    def update_user(
        self,
        user: User,
        data: UserUpdate,
    ) -> User:
        return self.repository.update(
            user,
            name=data.name,
        )

    def update_avatar(
        self,
        user: User,
        *,
        content: bytes,
        content_type: str | None,
    ) -> User:
        if content_type not in ALLOWED_AVATAR_TYPES:
            raise ValueError("Avatar must be a JPEG, PNG or WebP image")

        if len(content) > MAX_AVATAR_SIZE:
            raise ValueError("Avatar must not exceed 2 MB")

        if not content:
            raise ValueError("Avatar file is empty")

        AVATAR_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = ALLOWED_AVATAR_TYPES[content_type]
        filename = f"{uuid4().hex}{extension}"

        avatar_path = AVATAR_DIRECTORY / filename
        avatar_path.write_bytes(content)

        previous_filename = user.avatar_filename

        updated_user = self.repository.update_avatar(
            user,
            avatar_filename=filename,
        )

        if previous_filename:
            previous_path = AVATAR_DIRECTORY / previous_filename

            if previous_path.is_file():
                previous_path.unlink()

        return updated_user

    def remove_avatar(
        self,
        user: User,
    ) -> User:
        previous_filename = user.avatar_filename

        updated_user = self.repository.update_avatar(
            user,
            avatar_filename=None,
        )

        if previous_filename:
            previous_path = AVATAR_DIRECTORY / previous_filename

            if previous_path.is_file():
                previous_path.unlink()

        return updated_user
