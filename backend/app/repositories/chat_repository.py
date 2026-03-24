from sqlalchemy.orm import Session

from app.db.models import Chat


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        client_id: int,
        provider: str,
        external_chat_id: str | None,
        title: str | None,
    ) -> Chat:
        chat = Chat(
            client_id=client_id,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
        )
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_by_id(self, chat_id: int) -> Chat | None:
        return self.db.get(Chat, chat_id)

    def list(self, skip: int = 0, limit: int = 100) -> list[Chat]:
        return self.db.query(Chat).offset(skip).limit(limit).all()

    def update(
        self,
        chat: Chat,
        provider: str | None = None,
        external_chat_id: str | None = None,
        title: str | None = None,
    ) -> Chat:
        if provider is not None:
            chat.provider = provider
        if external_chat_id is not None:
            chat.external_chat_id = external_chat_id
        if title is not None:
            chat.title = title
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def delete(self, chat: Chat) -> None:
        self.db.delete(chat)
        self.db.commit()

