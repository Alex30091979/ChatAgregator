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
        operator_id: int | None = None,
        status: str = "new",
    ) -> Chat:
        chat = Chat(
            client_id=client_id,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
            operator_id=operator_id,
            status=status,
        )
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_by_id(self, chat_id: int) -> Chat | None:
        return self.db.get(Chat, chat_id)

    def list(
        self,
        status: str | None = None,
        operator_id: int | None = None,
        channel: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Chat]:
        query = self.db.query(Chat)
        if status is not None:
            query = query.filter(Chat.status == status)
        if operator_id is not None:
            query = query.filter(Chat.operator_id == operator_id)
        if channel is not None:
            query = query.filter(Chat.provider == channel)
        return query.order_by(Chat.id.desc()).offset(skip).limit(limit).all()

    def update(
        self,
        chat: Chat,
        provider: str | None = None,
        external_chat_id: str | None = None,
        title: str | None = None,
        operator_id: int | None = None,
        status: str | None = None,
    ) -> Chat:
        if provider is not None:
            chat.provider = provider
        if external_chat_id is not None:
            chat.external_chat_id = external_chat_id
        if title is not None:
            chat.title = title
        if operator_id is not None:
            chat.operator_id = operator_id
        if status is not None:
            chat.status = status
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def assign_operator(self, chat: Chat, operator_id: int) -> Chat:
        chat.operator_id = operator_id
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def change_status(self, chat: Chat, status: str) -> Chat:
        chat.status = status
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def delete(self, chat: Chat) -> None:
        self.db.delete(chat)
        self.db.commit()

