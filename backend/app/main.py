import uvicorn
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.dependencies import (
    get_auth_service,
    get_chat_service,
    get_db,
    get_message_service,
    require_roles,
)
from app.middleware.auth_middleware import AuthContextMiddleware
from app.repositories.user_repository import UserRepository
from app.realtime.connection_manager import connection_manager
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.chat import (
    ChatAssignOperator,
    ChatCreate,
    ChatRead,
    ChatStatusUpdate,
    ChatUpdate,
)
from app.schemas.message import MessageCreate, MessageRead, MessageUpdate
from app.schemas.realtime import TypingEventRequest
from app.security import decode_access_token
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.message_service import MessageService

app = FastAPI(title="chat-aggregator-backend")
app.add_middleware(AuthContextMiddleware)


@app.on_event("startup")
def bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        auth_service = AuthService(
            user_repository=UserRepository(db),
            settings=get_settings(),
        )
        auth_service.ensure_bootstrap_admin()
    except Exception:
        pass
    finally:
        db.close()


@app.get("/health")
def health(
    db: Session = Depends(get_db), _: Settings = Depends(get_settings)
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    payload = decode_access_token(token or "")
    if payload is None:
        await websocket.close(code=1008)
        return

    user_id = payload.get("uid")
    role = payload.get("role")
    if not isinstance(user_id, int) or not isinstance(role, str):
        await websocket.close(code=1008)
        return

    chat_ids: set[int] = set()
    for value in websocket.query_params.getlist("chat_id"):
        try:
            chat_ids.add(int(value))
        except ValueError:
            continue

    connection_id = await connection_manager.connect(
        websocket=websocket,
        user_id=user_id,
        role=role,
        chat_ids=chat_ids,
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(connection_id)


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    token = auth_service.login(username=payload.username, password=payload.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(access_token=token)


@app.post("/chats", response_model=ChatRead)
def create_chat(
    payload: ChatCreate,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin", "manager"})),
) -> ChatRead:
    try:
        chat = service.create_chat(
            client_id=payload.client_id,
            provider=payload.provider,
            external_chat_id=payload.external_chat_id,
            title=payload.title,
            operator_id=payload.operator_id,
            status=payload.status,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatRead.model_validate(chat)


@app.get("/chats", response_model=list[ChatRead])
def list_chats(
    status: str | None = None,
    operator_id: int | None = None,
    channel: str | None = None,
    skip: int = 0,
    limit: int = 100,
    service: ChatService = Depends(get_chat_service),
    _: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> list[ChatRead]:
    chats = service.list_chats(
        status=status,
        operator_id=operator_id,
        channel=channel,
        skip=skip,
        limit=limit,
    )
    return [ChatRead.model_validate(chat) for chat in chats]


@app.get("/chats/{chat_id}", response_model=ChatRead)
def get_chat(
    chat_id: int,
    service: ChatService = Depends(get_chat_service),
    _: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> ChatRead:
    chat = service.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatRead.model_validate(chat)


@app.put("/chats/{chat_id}", response_model=ChatRead)
def update_chat(
    chat_id: int,
    payload: ChatUpdate,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin", "manager"})),
) -> ChatRead:
    try:
        chat = service.update_chat(
            chat_id=chat_id,
            provider=payload.provider,
            external_chat_id=payload.external_chat_id,
            title=payload.title,
            operator_id=payload.operator_id,
            status=payload.status,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatRead.model_validate(chat)


@app.post("/chats/{chat_id}/assign-operator", response_model=ChatRead)
async def assign_operator(
    chat_id: int,
    payload: ChatAssignOperator,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin", "manager"})),
) -> ChatRead:
    chat = service.assign_operator(
        chat_id=chat_id,
        operator_id=payload.operator_id,
        actor_user_id=current_user.id,
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat or operator not found")
    await connection_manager.broadcast(
        event="chat_assigned",
        payload={"chat_id": chat.id, "operator_id": chat.operator_id, "assigned_by": current_user.id},
    )
    return ChatRead.model_validate(chat)


@app.post("/chats/{chat_id}/status", response_model=ChatRead)
async def change_chat_status(
    chat_id: int,
    payload: ChatStatusUpdate,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> ChatRead:
    try:
        chat = service.change_status(
            chat_id=chat_id,
            status=payload.status,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    await connection_manager.broadcast(
        event="status_changed",
        payload={"chat_id": chat.id, "status": chat.status, "changed_by": current_user.id},
    )
    return ChatRead.model_validate(chat)


@app.post("/chats/{chat_id}/typing")
async def typing_event(
    chat_id: int,
    payload: TypingEventRequest,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> dict[str, bool]:
    chat = service.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    await connection_manager.broadcast(
        event="typing",
        payload={
            "chat_id": chat_id,
            "user_id": current_user.id,
            "is_typing": payload.is_typing,
        },
    )
    return {"ok": True}


@app.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: int,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(require_roles({"admin"})),
) -> dict[str, bool]:
    deleted = service.delete_chat(chat_id, actor_user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"deleted": True}


@app.post("/messages", response_model=MessageRead)
async def create_message(
    payload: MessageCreate,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> MessageRead:
    user_id = payload.user_id
    if current_user.role == "operator":
        user_id = current_user.id
    message = service.create_message(chat_id=payload.chat_id, user_id=user_id, body=payload.body)
    if message is None:
        raise HTTPException(status_code=400, detail="Invalid chat_id or user_id")
    await connection_manager.broadcast(
        event="new_message",
        payload={
            "chat_id": message.chat_id,
            "message_id": message.id,
            "user_id": message.user_id,
            "body": message.body,
            "created_at": message.created_at.isoformat(),
        },
    )
    return MessageRead.model_validate(message)


@app.get("/messages", response_model=list[MessageRead])
def list_messages(
    chat_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    service: MessageService = Depends(get_message_service),
    _: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> list[MessageRead]:
    messages = service.list_messages(chat_id=chat_id, skip=skip, limit=limit)
    return [MessageRead.model_validate(message) for message in messages]


@app.get("/messages/{message_id}", response_model=MessageRead)
def get_message(
    message_id: int,
    service: MessageService = Depends(get_message_service),
    _: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> MessageRead:
    message = service.get_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageRead.model_validate(message)


@app.put("/messages/{message_id}", response_model=MessageRead)
def update_message(
    message_id: int,
    payload: MessageUpdate,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(require_roles({"admin", "manager"})),
) -> MessageRead:
    message = service.update_message(
        message_id=message_id,
        body=payload.body,
        actor_user_id=current_user.id,
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageRead.model_validate(message)


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(require_roles({"admin", "manager"})),
) -> dict[str, bool]:
    deleted = service.delete_message(message_id, actor_user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"deleted": True}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)

