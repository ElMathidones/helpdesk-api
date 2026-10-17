from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from app.schemas.user import UserCreate, UserEmailUpdate
from app.services.user import UserService


def create_test_user(db):
    service = UserService(db)

    user = service.create_user(
        UserCreate(
            name="Usuário Teste",
            email="original@example.com",
            password="senha123",
        )
    )

    return service, user


def test_email_change_creates_pending_request(db):
    service, user = create_test_user(db)

    token, new_email = service.request_email_change(
        user,
        UserEmailUpdate(
            email="novo@example.com",
            current_password="senha123",
        ),
    )

    assert new_email == "novo@example.com"
    assert user.email == "original@example.com"
    assert user.pending_email == "novo@example.com"
    assert user.email_change_token_hash == sha256(token.encode("utf-8")).hexdigest()
    assert user.email_change_expires_at is not None


def test_email_change_requires_correct_password(db):
    service, user = create_test_user(db)

    with pytest.raises(PermissionError):
        service.request_email_change(
            user,
            UserEmailUpdate(
                email="novo@example.com",
                current_password="senha_errada",
            ),
        )

    assert user.email == "original@example.com"
    assert user.pending_email is None


def test_email_change_confirmation_is_single_use(db):
    service, user = create_test_user(db)

    token, _ = service.request_email_change(
        user,
        UserEmailUpdate(
            email="novo@example.com",
            current_password="senha123",
        ),
    )

    updated_user = service.confirm_email_change(token)

    assert updated_user.email == "novo@example.com"
    assert updated_user.pending_email is None
    assert updated_user.email_change_token_hash is None

    with pytest.raises(ValueError):
        service.confirm_email_change(token)


def test_expired_email_change_token_is_rejected(db):
    service, user = create_test_user(db)

    token, _ = service.request_email_change(
        user,
        UserEmailUpdate(
            email="novo@example.com",
            current_password="senha123",
        ),
    )

    user.email_change_expires_at = datetime.now(UTC) - timedelta(minutes=1)

    db.commit()

    with pytest.raises(ValueError):
        service.confirm_email_change(token)

    db.refresh(user)

    assert user.email == "original@example.com"


def test_email_change_respects_cooldown(db):
    service, user = create_test_user(db)

    service.request_email_change(
        user,
        UserEmailUpdate(
            email="primeiro@example.com",
            current_password="senha123",
        ),
    )

    with pytest.raises(ValueError):
        service.request_email_change(
            user,
            UserEmailUpdate(
                email="segundo@example.com",
                current_password="senha123",
            ),
        )

    db.refresh(user)

    assert user.pending_email == "primeiro@example.com"


def test_email_change_locks_after_five_wrong_passwords(db):
    service, user = create_test_user(db)

    for _ in range(4):
        with pytest.raises(
            PermissionError,
            match="Incorrect current password",
        ):
            service.request_email_change(
                user,
                UserEmailUpdate(
                    email="novo@example.com",
                    current_password="senha_errada",
                ),
            )

    with pytest.raises(
        PermissionError,
        match="Email change temporarily locked",
    ):
        service.request_email_change(
            user,
            UserEmailUpdate(
                email="novo@example.com",
                current_password="senha_errada",
            ),
        )

    db.refresh(user)

    assert user.email_change_failed_attempts == 5
    assert user.email_change_locked_until is not None
    assert user.pending_email is None

    with pytest.raises(
        PermissionError,
        match="Email change temporarily locked",
    ):
        service.request_email_change(
            user,
            UserEmailUpdate(
                email="novo@example.com",
                current_password="senha123",
            ),
        )


def test_correct_password_resets_failed_attempts(db):
    service, user = create_test_user(db)

    for _ in range(2):
        with pytest.raises(PermissionError):
            service.request_email_change(
                user,
                UserEmailUpdate(
                    email="novo@example.com",
                    current_password="senha_errada",
                ),
            )

    db.refresh(user)
    assert user.email_change_failed_attempts == 2

    service.request_email_change(
        user,
        UserEmailUpdate(
            email="novo@example.com",
            current_password="senha123",
        ),
    )

    db.refresh(user)

    assert user.email_change_failed_attempts == 0
    assert user.email_change_locked_until is None
    assert user.pending_email == "novo@example.com"


def test_email_change_lock_expires(db):
    service, user = create_test_user(db)

    for _ in range(5):
        with pytest.raises(PermissionError):
            service.request_email_change(
                user,
                UserEmailUpdate(
                    email="novo@example.com",
                    current_password="senha_errada",
                ),
            )

    user.email_change_locked_until = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    token, new_email = service.request_email_change(
        user,
        UserEmailUpdate(
            email="novo@example.com",
            current_password="senha123",
        ),
    )

    assert token
    assert new_email == "novo@example.com"

    db.refresh(user)

    assert user.email_change_failed_attempts == 0
    assert user.email_change_locked_until is None
