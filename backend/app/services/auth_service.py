from app.config import Settings
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.security import create_access_token, hash_password, verify_password

VALID_ROLES = {"admin", "manager", "operator"}


class AuthService:
    def __init__(self, user_repository: UserRepository, settings: Settings) -> None:
        self.user_repository = user_repository
        self.settings = settings

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.user_repository.get_by_username(username=username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def login(self, username: str, password: str) -> str | None:
        user = self.authenticate(username=username, password=password)
        if user is None:
            return None
        return create_access_token(subject=user.username, user_id=user.id, role=user.role)

    def ensure_bootstrap_admin(self) -> None:
        existing = self.user_repository.get_by_username(self.settings.bootstrap_admin_username)
        if existing is not None:
            return

        self.user_repository.create(
            username=self.settings.bootstrap_admin_username,
            password_hash=hash_password(self.settings.bootstrap_admin_password),
            role="admin",
            full_name="Bootstrap Admin",
        )

