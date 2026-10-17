from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserEmailUpdate, UserUpdate

AVATAR_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads" / "avatars"

ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_AVATAR_SIZE = 2 * 1024 * 1024


def is_valid_avatar_content(
    content: bytes,
    content_type: str,
) -> bool:
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")

    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")

    if content_type == "image/webp":
        return (
            len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
        )

    return False


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

    def update_email(
        self,
        user: User,
        data: UserEmailUpdate,
    ) -> User:
        if not verify_password(
            data.current_password,
            user.password_hash,
        ):
            raise PermissionError("Incorrect current password")

        new_email = str(data.email).strip().lower()

        if new_email == user.email.lower():
            return user

        existing_user = self.repository.get_by_email(new_email)

        if existing_user is not None and existing_user.id != user.id:
            raise ValueError("Email already registered")

        return self.repository.update_email(
            user,
            email=new_email,
        )

    def request_email_change(
        self,
        user: User,
        data: UserEmailUpdate,
    ) -> tuple[str, str]:
        settings = get_settings()
        now = datetime.now(UTC)

        password_valid = verify_password(
            data.current_password,
            user.password_hash,
        )

        self.repository.check_email_change_password(
            user,
            password_valid=password_valid,
            now=now,
            max_attempts=settings.email_change_max_password_attempts,
            lock_minutes=settings.email_change_lock_minutes,
        )

        new_email = str(data.email).strip().lower()

        if new_email == user.email.lower():
            raise ValueError("New email must be different")

        existing_user = self.repository.get_by_email(new_email)

        if existing_user is not None and existing_user.id != user.id:
            raise ValueError("Email already registered")

        token = token_urlsafe(32)

        token_hash = sha256(token.encode("utf-8")).hexdigest()

        expires_at = now + timedelta(minutes=settings.email_change_token_expire_minutes)

        self.repository.stage_email_change(
            user,
            pending_email=new_email,
            token_hash=token_hash,
            requested_at=now,
            expires_at=expires_at,
            cooldown_seconds=settings.email_change_cooldown_seconds,
        )

        return token, new_email

    def confirm_email_change(
        self,
        token: str,
    ) -> User:
        if not token or len(token) > 256:
            raise ValueError("Invalid or expired confirmation token")

        token_hash = sha256(token.encode("utf-8")).hexdigest()

        return self.repository.confirm_email_change(
            token_hash=token_hash,
            now=datetime.now(UTC),
        )

    def cancel_email_change_request(
        self,
        token: str,
    ) -> None:
        token_hash = sha256(token.encode("utf-8")).hexdigest()

        self.repository.cancel_email_change_request(
            token_hash=token_hash,
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

        if not is_valid_avatar_content(content, content_type):
            raise ValueError("Avatar content does not match its file type")

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
