from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

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


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
def chat_with_assistant(
    data: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
) -> AssistantChatResponse:
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
