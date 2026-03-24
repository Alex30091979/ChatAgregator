from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
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
    user_repository = UserRepository(db)
    audit_service = AuditService(db)
    return ChatService(
        chat_repository=chat_repository,
        user_repository=user_repository,
        audit_service=audit_service,
    )


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


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    settings = get_settings()
    return AuthService(user_repository=user_repository, settings=settings)


def get_current_user(
    request: Request,
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    payload = getattr(request.state, "user", None)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = payload.get("uid")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(allowed_roles: set[str]):
    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _guard

