from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(
        self,
        ticket_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        self.active_connections.setdefault(ticket_id, set()).add(websocket)

    def disconnect(
        self,
        ticket_id: int,
        websocket: WebSocket,
    ) -> None:
        connections = self.active_connections.get(ticket_id)

        if connections is None:
            return

        connections.discard(websocket)

        if not connections:
            del self.active_connections[ticket_id]

    async def broadcast(
        self,
        ticket_id: int,
        message: dict,
    ) -> None:
        connections = self.active_connections.get(ticket_id, set())

        for websocket in connections:
            await websocket.send_json(message)


manager = ConnectionManager()
