from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.user import (
    EmailChangeConfirm,
    EmailChangeStatus,
    UserCreate,
    UserEmailUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.email import EmailDeliveryError, EmailService
from app.services.user import (
    AVATAR_DIRECTORY,
    MAX_AVATAR_SIZE,
    UserService,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    try:
        user = service.create_user(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return user


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_current_user(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    service = UserService(db)
    return service.update_user(current_user, data)


@router.patch(
    "/me/email",
    response_model=EmailChangeStatus,
    status_code=status.HTTP_202_ACCEPTED,
)
def update_current_user_email(
    data: UserEmailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailChangeStatus:
    service = UserService(db)

    try:
        token, new_email = service.request_email_change(
            current_user,
            data,
        )

    except PermissionError as exc:
        message = str(exc)

        if message == "Email change temporarily locked":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect current password",
        ) from exc

    except ValueError as exc:
        message = str(exc)

        if message == "Email already registered":
            code = status.HTTP_409_CONFLICT

        elif message == "Please wait before requesting again":
            code = status.HTTP_429_TOO_MANY_REQUESTS

        else:
            code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=code,
            detail=message,
        ) from exc

    try:
        EmailService().send_email_change_confirmation(
            recipient_email=new_email,
            recipient_name=current_user.name,
            token=token,
        )

    except EmailDeliveryError as exc:
        service.cancel_email_change_request(token)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send confirmation email",
        ) from exc

    return EmailChangeStatus(
        message="Confirmation email sent",
    )


@router.post(
    "/confirm-email",
    response_model=EmailChangeStatus,
)
def confirm_user_email_change(
    data: EmailChangeConfirm,
    db: Session = Depends(get_db),
) -> EmailChangeStatus:
    service = UserService(db)

    try:
        service.confirm_email_change(data.token)

    except ValueError as exc:
        if str(exc) == "Email already registered":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token",
        ) from exc

    return EmailChangeStatus(
        message="Email updated successfully",
    )


@router.post(
    "/me/avatar",
    response_model=UserResponse,
)
async def upload_current_user_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    service = UserService(db)

    content = await avatar.read(MAX_AVATAR_SIZE + 1)

    try:
        return service.update_avatar(
            current_user,
            content=content,
            content_type=avatar.content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/me/avatar",
    response_model=UserResponse,
)
def remove_current_user_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    service = UserService(db)

    return service.remove_avatar(current_user)


@router.get(
    "/avatars/{filename}",
)
def read_avatar(filename: str) -> FileResponse:
    safe_filename = Path(filename).name

    if safe_filename != filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )

    avatar_path = AVATAR_DIRECTORY / safe_filename

    if not avatar_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )

    return FileResponse(
        avatar_path,
        headers={
            "X-Content-Type-Options": "nosniff",
        },
    )
