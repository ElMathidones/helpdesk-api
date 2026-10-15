from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import FailedAttemptRateLimiter
from app.core.security import create_access_token, verify_password
from app.dependencies.database import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

login_rate_limiter = FailedAttemptRateLimiter(
    max_attempts=5,
    window_seconds=300,
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    repository = UserRepository(db)

    client_ip = request.client.host if request.client is not None else "unknown"

    rate_limit_key = f"{client_ip}:{form_data.username.strip().lower()}"

    retry_after = login_rate_limiter.get_retry_after(rate_limit_key)

    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={
                "Retry-After": str(retry_after),
            },
        )

    user = repository.get_by_email(form_data.username)

    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        login_rate_limiter.register_failure(rate_limit_key)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_rate_limiter.reset(rate_limit_key)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
    )
