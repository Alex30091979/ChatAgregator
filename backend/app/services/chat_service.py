from app.db.models import Chat
from app.repositories.chat_repository import ChatRepository
from app.services.audit_service import AuditService


class ChatService:
    def __init__(self, chat_repository: ChatRepository, audit_service: AuditService) -> None:
        self.chat_repository = chat_repository
        self.audit_service = audit_service

    def create_chat(
        self,
        client_id: int,
        provider: str,
        external_chat_id: str | None,
        title: str | None,
        actor_user_id: int | None = None,
    ) -> Chat:
        chat = self.chat_repository.create(
            client_id=client_id,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
        )
        self.audit_service.log(
            action="chat.created",
            entity_type="chat",
            entity_id=str(chat.id),
            user_id=actor_user_id,
        )
        return chat

    def get_chat(self, chat_id: int) -> Chat | None:
        return self.chat_repository.get_by_id(chat_id)

    def list_chats(self, skip: int = 0, limit: int = 100) -> list[Chat]:
        return self.chat_repository.list(skip=skip, limit=limit)

    def update_chat(
        self,
        chat_id: int,
        provider: str | None = None,
        external_chat_id: str | None = None,
        title: str | None = None,
        actor_user_id: int | None = None,
    ) -> Chat | None:
        chat = self.chat_repository.get_by_id(chat_id)
        if chat is None:
            return None

        updated = self.chat_repository.update(
            chat=chat,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
        )
        self.audit_service.log(
            action="chat.updated",
            entity_type="chat",
            entity_id=str(updated.id),
            user_id=actor_user_id,
        )
        return updated

    def delete_chat(self, chat_id: int, actor_user_id: int | None = None) -> bool:
        chat = self.chat_repository.get_by_id(chat_id)
        if chat is None:
            return False

        self.chat_repository.delete(chat)
        self.audit_service.log(
            action="chat.deleted",
            entity_type="chat",
            entity_id=str(chat_id),
            user_id=actor_user_id,
        )
        return True

