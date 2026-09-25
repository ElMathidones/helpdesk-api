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
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    db: Session = SessionLocal()

    try:
        try:
            current_user = get_user_from_token(
                token=token,
                db=db,
            )
        except ValueError, PermissionError:
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

        await manager.connect(ticket_id, websocket)

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
            manager.disconnect(ticket_id, websocket)

    finally:
        db.close()
