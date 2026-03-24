from sqlalchemy.orm import Session

from app.db.models import Message


class MessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, chat_id: int, user_id: int, body: str) -> Message:
        message = Message(chat_id=chat_id, user_id=user_id, body=body)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_id(self, message_id: int) -> Message | None:
        return self.db.get(Message, message_id)

    def list(self, chat_id: int | None = None, skip: int = 0, limit: int = 100) -> list[Message]:
        query = self.db.query(Message)
        if chat_id is not None:
            query = query.filter(Message.chat_id == chat_id)
        return query.order_by(Message.id.desc()).offset(skip).limit(limit).all()

    def update(self, message: Message, body: str) -> Message:
        message.body = body
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete(self, message: Message) -> None:
        self.db.delete(message)
        self.db.commit()

