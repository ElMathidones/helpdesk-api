from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == email.strip().lower())
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

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError("Email already registered") from exc

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

    def update_email(
        self,
        user: User,
        *,
        email: str,
    ) -> User:
        user.email = email

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Email already registered") from exc

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

    def stage_email_change(
        self,
        user: User,
        *,
        pending_email: str,
        token_hash: str,
        requested_at: datetime,
        expires_at: datetime,
        cooldown_seconds: int,
    ) -> None:
        statement = (
            select(User)
            .where(User.id == user.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        current_user = self.db.scalar(statement)

        if current_user is None:
            self.db.rollback()
            raise ValueError("User not found")

        locked_until = current_user.email_change_locked_until

        if locked_until is not None and as_utc(locked_until) > requested_at:
            self.db.rollback()
            raise PermissionError("Email change temporarily locked")

        if current_user.email.lower() == pending_email.lower():
            self.db.rollback()
            raise ValueError("New email must be different")

        last_request = current_user.email_change_requested_at

        if last_request is not None:
            elapsed = (requested_at - as_utc(last_request)).total_seconds()

            if elapsed < cooldown_seconds:
                self.db.rollback()
                raise ValueError("Please wait before requesting again")

        current_user.pending_email = pending_email
        current_user.email_change_token_hash = token_hash
        current_user.email_change_requested_at = requested_at
        current_user.email_change_expires_at = expires_at

        self.db.commit()
        self.db.refresh(current_user)

    def confirm_email_change(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> User:
        statement = (
            select(User)
            .where(User.email_change_token_hash == token_hash)
            .with_for_update()
        )

        user = self.db.scalar(statement)

        if (
            user is None
            or user.pending_email is None
            or user.email_change_expires_at is None
        ):
            self.db.rollback()
            raise ValueError("Invalid or expired confirmation token")

        if as_utc(user.email_change_expires_at) <= now:
            self.db.rollback()
            raise ValueError("Invalid or expired confirmation token")

        existing_user = self.get_by_email(user.pending_email)

        if existing_user is not None and existing_user.id != user.id:
            self.db.rollback()
            raise ValueError("Email already registered")

        user.email = user.pending_email
        user.pending_email = None
        user.email_change_token_hash = None
        user.email_change_expires_at = None
        user.email_change_requested_at = None

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Email already registered") from exc

        self.db.refresh(user)

        return user

    def cancel_email_change_request(
        self,
        *,
        token_hash: str,
    ) -> None:
        statement = (
            select(User)
            .where(User.email_change_token_hash == token_hash)
            .with_for_update()
        )

        user = self.db.scalar(statement)

        if user is None:
            self.db.rollback()
            return

        user.pending_email = None
        user.email_change_token_hash = None
        user.email_change_expires_at = None

        self.db.commit()

    def check_email_change_password(
        self,
        user: User,
        *,
        password_valid: bool,
        now: datetime,
        max_attempts: int,
        lock_minutes: int,
    ) -> None:
        statement = (
            select(User)
            .where(User.id == user.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        current_user = self.db.scalar(statement)

        if current_user is None:
            self.db.rollback()
            raise ValueError("User not found")

        locked_until = current_user.email_change_locked_until

        if locked_until is not None:
            if as_utc(locked_until) > now:
                self.db.rollback()
                raise PermissionError("Email change temporarily locked")

            current_user.email_change_locked_until = None
            current_user.email_change_failed_attempts = 0

        if password_valid:
            current_user.email_change_failed_attempts = 0
            current_user.email_change_locked_until = None
            self.db.commit()
            return

        attempts = current_user.email_change_failed_attempts + 1
        current_user.email_change_failed_attempts = attempts

        if attempts >= max_attempts:
            current_user.email_change_locked_until = now + timedelta(
                minutes=lock_minutes
            )

            error_message = "Email change temporarily locked"
        else:
            error_message = "Incorrect current password"

        self.db.commit()

        raise PermissionError(error_message)
