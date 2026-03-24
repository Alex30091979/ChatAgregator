import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_chat_service, get_db, get_message_service
from app.schemas.chat import ChatCreate, ChatRead, ChatUpdate
from app.schemas.message import MessageCreate, MessageRead, MessageUpdate
from app.services.chat_service import ChatService
from app.services.message_service import MessageService

app = FastAPI(title="chat-aggregator-backend")


@app.get("/health")
def health(
    db: Session = Depends(get_db), _: Settings = Depends(get_settings)
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/chats", response_model=ChatRead)
def create_chat(payload: ChatCreate, service: ChatService = Depends(get_chat_service)) -> ChatRead:
    chat = service.create_chat(
        client_id=payload.client_id,
        provider=payload.provider,
        external_chat_id=payload.external_chat_id,
        title=payload.title,
        actor_user_id=payload.actor_user_id,
    )
    return ChatRead.model_validate(chat)


@app.get("/chats", response_model=list[ChatRead])
def list_chats(
    skip: int = 0,
    limit: int = 100,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatRead]:
    chats = service.list_chats(skip=skip, limit=limit)
    return [ChatRead.model_validate(chat) for chat in chats]


@app.get("/chats/{chat_id}", response_model=ChatRead)
def get_chat(chat_id: int, service: ChatService = Depends(get_chat_service)) -> ChatRead:
    chat = service.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatRead.model_validate(chat)


@app.put("/chats/{chat_id}", response_model=ChatRead)
def update_chat(
    chat_id: int,
    payload: ChatUpdate,
    service: ChatService = Depends(get_chat_service),
) -> ChatRead:
    chat = service.update_chat(
        chat_id=chat_id,
        provider=payload.provider,
        external_chat_id=payload.external_chat_id,
        title=payload.title,
        actor_user_id=payload.actor_user_id,
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatRead.model_validate(chat)


@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, service: ChatService = Depends(get_chat_service)) -> dict[str, bool]:
    deleted = service.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"deleted": True}


@app.post("/messages", response_model=MessageRead)
def create_message(
    payload: MessageCreate, service: MessageService = Depends(get_message_service)
) -> MessageRead:
    message = service.create_message(chat_id=payload.chat_id, user_id=payload.user_id, body=payload.body)
    if message is None:
        raise HTTPException(status_code=400, detail="Invalid chat_id or user_id")
    return MessageRead.model_validate(message)


@app.get("/messages", response_model=list[MessageRead])
def list_messages(
    chat_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    service: MessageService = Depends(get_message_service),
) -> list[MessageRead]:
    messages = service.list_messages(chat_id=chat_id, skip=skip, limit=limit)
    return [MessageRead.model_validate(message) for message in messages]


@app.get("/messages/{message_id}", response_model=MessageRead)
def get_message(message_id: int, service: MessageService = Depends(get_message_service)) -> MessageRead:
    message = service.get_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageRead.model_validate(message)


@app.put("/messages/{message_id}", response_model=MessageRead)
def update_message(
    message_id: int,
    payload: MessageUpdate,
    service: MessageService = Depends(get_message_service),
) -> MessageRead:
    message = service.update_message(
        message_id=message_id,
        body=payload.body,
        actor_user_id=payload.actor_user_id,
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageRead.model_validate(message)


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int, service: MessageService = Depends(get_message_service)
) -> dict[str, bool]:
    deleted = service.delete_message(message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"deleted": True}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)

