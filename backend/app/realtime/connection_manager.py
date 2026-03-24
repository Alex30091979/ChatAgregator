from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class Connection:
    websocket: WebSocket
    user_id: int
    role: str
    chat_ids: set[int] = field(default_factory=set)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, Connection] = {}
        self._next_id = 1

    async def connect(self, websocket: WebSocket, user_id: int, role: str, chat_ids: set[int] | None = None) -> int:
        await websocket.accept()
        connection_id = self._next_id
        self._next_id += 1
        self._connections[connection_id] = Connection(
            websocket=websocket,
            user_id=user_id,
            role=role,
            chat_ids=chat_ids or set(),
        )
        return connection_id

    def disconnect(self, connection_id: int) -> None:
        self._connections.pop(connection_id, None)

    async def broadcast(self, event: str, payload: dict) -> None:
        stale_ids: list[int] = []
        chat_id = payload.get("chat_id")
        for conn_id, connection in self._connections.items():
            if isinstance(chat_id, int) and connection.chat_ids and chat_id not in connection.chat_ids:
                continue
            try:
                await connection.websocket.send_json({"event": event, "payload": payload})
            except Exception:
                stale_ids.append(conn_id)
        for conn_id in stale_ids:
            self.disconnect(conn_id)


connection_manager = ConnectionManager()

