from app.db.models import Message
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class MessageService:
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        audit_service: AuditService,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.user_repository = user_repository
        self.audit_service = audit_service

    def create_message(self, chat_id: int, user_id: int, body: str) -> Message | None:
        chat = self.chat_repository.get_by_id(chat_id)
        user = self.user_repository.get_by_id(user_id)
        if chat is None or user is None:
            return None

        message = self.message_repository.create(chat_id=chat_id, user_id=user_id, body=body)
        self.audit_service.log(
            action="message.created",
            entity_type="message",
            entity_id=str(message.id),
            user_id=user_id,
            payload={"chat_id": chat_id},
        )
        return message

    def get_message(self, message_id: int) -> Message | None:
        return self.message_repository.get_by_id(message_id)

    def list_messages(self, chat_id: int | None = None, skip: int = 0, limit: int = 100) -> list[Message]:
        return self.message_repository.list(chat_id=chat_id, skip=skip, limit=limit)

    def update_message(self, message_id: int, body: str, actor_user_id: int | None = None) -> Message | None:
        message = self.message_repository.get_by_id(message_id)
        if message is None:
            return None

        updated = self.message_repository.update(message=message, body=body)
        self.audit_service.log(
            action="message.updated",
            entity_type="message",
            entity_id=str(updated.id),
            user_id=actor_user_id,
        )
        return updated

    def delete_message(self, message_id: int, actor_user_id: int | None = None) -> bool:
        message = self.message_repository.get_by_id(message_id)
        if message is None:
            return False

        self.message_repository.delete(message)
        self.audit_service.log(
            action="message.deleted",
            entity_type="message",
            entity_id=str(message_id),
            user_id=actor_user_id,
        )
        return True

