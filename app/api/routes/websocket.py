import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.dependencies.auth import get_user_from_token
from app.services.ticket import TicketService
from app.services.websocket import manager

router = APIRouter(tags=["websocket"])

settings = get_settings()


@router.websocket("/ws/tickets/{ticket_id}")
async def ticket_websocket(
    websocket: WebSocket,
    ticket_id: int,
) -> None:
    origin = websocket.headers.get("origin")

    allowed_origins = {
        item.strip() for item in settings.cors_origins.split(",") if item.strip()
    }

    if origin is not None and origin not in allowed_origins:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    db: Session = SessionLocal()

    try:
        try:
            auth_message = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=5,
            )

            if not isinstance(auth_message, dict):
                await websocket.close(code=1008)
                return

            if auth_message.get("type") != "auth":
                await websocket.close(code=1008)
                return

            token = auth_message.get("token")

            if not isinstance(token, str) or not token:
                await websocket.close(code=1008)
                return

            current_user = get_user_from_token(
                token=token,
                db=db,
            )
        except (
            TimeoutError,
            ValueError,
            PermissionError,
            WebSocketDisconnect,
        ):
            await websocket.close(code=1008)
            return

        ticket_service = TicketService(db)

        try:
            ticket_service.get_ticket(
                ticket_id=ticket_id,
                current_user=current_user,
            )
        except ValueError, PermissionError:
            await websocket.close(code=1008)
            return

        manager.connect(
            ticket_id,
            websocket,
        )

        try:
            while True:
                message = await websocket.receive_text()

                await manager.broadcast(
                    ticket_id=ticket_id,
                    message={
                        "type": "message",
                        "content": message,
                    },
                )
        except WebSocketDisconnect:
            manager.disconnect(
                ticket_id,
                websocket,
            )

    finally:
        db.close()
