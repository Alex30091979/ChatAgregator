import uvicorn
from fastapi import Depends, FastAPI, HTTPException
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
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.chat import ChatCreate, ChatRead, ChatUpdate
from app.schemas.message import MessageCreate, MessageRead, MessageUpdate
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
    chat = service.create_chat(
        client_id=payload.client_id,
        provider=payload.provider,
        external_chat_id=payload.external_chat_id,
        title=payload.title,
        actor_user_id=current_user.id,
    )
    return ChatRead.model_validate(chat)


@app.get("/chats", response_model=list[ChatRead])
def list_chats(
    skip: int = 0,
    limit: int = 100,
    service: ChatService = Depends(get_chat_service),
    _: User = Depends(require_roles({"admin", "manager", "operator"})),
) -> list[ChatRead]:
    chats = service.list_chats(skip=skip, limit=limit)
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
    chat = service.update_chat(
        chat_id=chat_id,
        provider=payload.provider,
        external_chat_id=payload.external_chat_id,
        title=payload.title,
        actor_user_id=current_user.id,
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatRead.model_validate(chat)


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
def create_message(
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

