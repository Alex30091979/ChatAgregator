from app.db.models import Chat
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService

VALID_CHAT_STATUSES = {"new", "open", "pending", "closed"}


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        audit_service: AuditService,
    ) -> None:
        self.chat_repository = chat_repository
        self.user_repository = user_repository
        self.audit_service = audit_service

    def create_chat(
        self,
        client_id: int,
        provider: str,
        external_chat_id: str | None,
        title: str | None,
        operator_id: int | None = None,
        status: str = "new",
        actor_user_id: int | None = None,
    ) -> Chat:
        if status not in VALID_CHAT_STATUSES:
            raise ValueError("Invalid chat status")
        if operator_id is not None and self.user_repository.get_by_id(operator_id) is None:
            raise ValueError("Operator not found")
        chat = self.chat_repository.create(
            client_id=client_id,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
            operator_id=operator_id,
            status=status,
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

    def list_chats(
        self,
        status: str | None = None,
        operator_id: int | None = None,
        channel: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Chat]:
        return self.chat_repository.list(
            status=status,
            operator_id=operator_id,
            channel=channel,
            skip=skip,
            limit=limit,
        )

    def update_chat(
        self,
        chat_id: int,
        provider: str | None = None,
        external_chat_id: str | None = None,
        title: str | None = None,
        operator_id: int | None = None,
        status: str | None = None,
        actor_user_id: int | None = None,
    ) -> Chat | None:
        chat = self.chat_repository.get_by_id(chat_id)
        if chat is None:
            return None
        if status is not None and status not in VALID_CHAT_STATUSES:
            raise ValueError("Invalid chat status")
        if operator_id is not None and self.user_repository.get_by_id(operator_id) is None:
            raise ValueError("Operator not found")

        updated = self.chat_repository.update(
            chat=chat,
            provider=provider,
            external_chat_id=external_chat_id,
            title=title,
            operator_id=operator_id,
            status=status,
        )
        self.audit_service.log(
            action="chat.updated",
            entity_type="chat",
            entity_id=str(updated.id),
            user_id=actor_user_id,
        )
        return updated

    def assign_operator(
        self,
        chat_id: int,
        operator_id: int,
        actor_user_id: int | None = None,
    ) -> Chat | None:
        chat = self.chat_repository.get_by_id(chat_id)
        operator = self.user_repository.get_by_id(operator_id)
        if chat is None or operator is None or operator.role != "operator":
            return None

        updated = self.chat_repository.assign_operator(chat=chat, operator_id=operator_id)
        self.audit_service.log(
            action="chat.operator_assigned",
            entity_type="chat",
            entity_id=str(chat_id),
            user_id=actor_user_id,
            payload={"operator_id": operator_id},
        )
        return updated

    def change_status(
        self,
        chat_id: int,
        status: str,
        actor_user_id: int | None = None,
    ) -> Chat | None:
        if status not in VALID_CHAT_STATUSES:
            raise ValueError("Invalid chat status")

        chat = self.chat_repository.get_by_id(chat_id)
        if chat is None:
            return None

        updated = self.chat_repository.change_status(chat=chat, status=status)
        self.audit_service.log(
            action="chat.status_changed",
            entity_type="chat",
            entity_id=str(chat_id),
            user_id=actor_user_id,
            payload={"status": status},
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

