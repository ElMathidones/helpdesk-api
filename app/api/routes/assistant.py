from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.core.rate_limit import RequestRateLimiter
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
)
from app.services.assistant import AssistantService

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)

assistant_rate_limiter = RequestRateLimiter(
    max_requests=10,
    window_seconds=60,
)


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
def chat_with_assistant(
    data: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
) -> AssistantChatResponse:
    retry_after = assistant_rate_limiter.consume(str(current_user.id))

    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=("Too many assistant requests. " "Try again later."),
            headers={
                "Retry-After": str(retry_after),
            },
        )

    service = AssistantService()

    try:
        answer = service.answer_question(
            message=data.message,
            user_role=current_user.role.value,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistant is temporarily unavailable",
        ) from exc

    return AssistantChatResponse(
        answer=answer,
    )
