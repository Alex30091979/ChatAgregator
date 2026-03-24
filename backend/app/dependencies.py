from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.chat_service import ChatService
from app.services.message_service import MessageService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_chat_repository(db: Session = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    chat_repository = ChatRepository(db)
    audit_service = AuditService(db)
    return ChatService(chat_repository=chat_repository, audit_service=audit_service)


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    message_repository = MessageRepository(db)
    chat_repository = ChatRepository(db)
    user_repository = UserRepository(db)
    audit_service = AuditService(db)
    return MessageService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        user_repository=user_repository,
        audit_service=audit_service,
    )

