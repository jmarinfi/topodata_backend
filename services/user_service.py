from api.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from data.repositories.user_repository import UserRepository
from services.password_service import PasswordService
from services.token_service import TokenService


class UserService:
    """Servicio para la gestión de usuarios y autenticación."""

    def __init__(
        self,
        repository: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ) -> None:
        self.repository = repository
        self.password_service = password_service
        self.token_service = token_service

    def get_users(self) -> list[UserResponse]:
        users = self.repository.get_all()
        return [UserResponse.model_validate(u) for u in users]

    def get_user(self, user_id: int) -> UserResponse:
        user = self.repository.get(user_id)
        if not user:
            raise ValueError(f"Usuario con id {user_id} no encontrado.")
        return UserResponse.model_validate(user)

    def register(self, user_data: UserCreate) -> UserResponse:
        """Registra un nuevo usuario hasheando su contraseña."""
        if self.repository.exists_by_username(user_data.username):
            raise ValueError(
                f"El nombre de usuario '{user_data.username}' ya está en uso."
            )
        if self.repository.exists_by_email(user_data.email):
            raise ValueError(f"El email '{user_data.email}' ya está registrado.")

        attributes = {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": self.password_service.hash(user_data.password),
        }
        user = self.repository.create(attributes)
        self.repository.refresh(user)

        return UserResponse.model_validate(user)

    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Actualiza datos del usuario. Sólo modifica los campos enviados."""
        db_user = self.repository.get(user_id)
        if not db_user:
            raise ValueError(f"Usuario con id {user_id} no encontrado.")

        attributes: dict = {}
        if user_data.email is not None:
            if self.repository.exists_by_email(user_data.email):
                raise ValueError(f"El email '{user_data.email}' ya está en uso.")
            attributes["email"] = user_data.email

        if user_data.password is not None:
            attributes["hashed_password"] = self.password_service.hash(
                user_data.password
            )

        if user_data.is_active is not None:
            attributes["is_active"] = user_data.is_active

        if user_data.is_superuser is not None:
            attributes["is_superuser"] = user_data.is_superuser

        user = self.repository.update(db_user, attributes)
        self.repository.refresh(user)

        return UserResponse.model_validate(user)

    def delete_user(self, user_id: int) -> None:
        db_user = self.repository.get(user_id)
        if not db_user:
            raise ValueError(f"Usuario con id {user_id} no encontrado.")
        self.repository.delete(db_user)

    # --- Autenticación ---

    def login(self, credentials: LoginRequest) -> TokenResponse:
        """Valida las credenciales y devuelve un token JWT si son correctos."""
        user = self.repository.get_by_email(credentials.email)

        if not user or not self.password_service.verify(
            credentials.password, user.hashed_password
        ):
            raise ValueError("Credenciales incorrectas.")

        if not user.is_active:
            raise ValueError("La cuenta está desactivada.")

        token = self.token_service.create_access_token(
            user_id=user.id, username=user.username
        )

        return TokenResponse(access_token=token)
