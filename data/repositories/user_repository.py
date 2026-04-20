from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models.user import User
from data.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repositorio de usuarios con métodos de búsqueda por credenciales."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=User, session=session)

    def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario."""
        return self._session.scalars(
            select(User).where(User.username == username)
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email."""
        return self._session.scalars(select(User).where(User.email == email)).first()

    def exists_by_username(self, username: str) -> bool:
        """Comprueba si ya existe un usuario con ese nombre."""
        return self.get_by_username(username) is not None

    def exists_by_email(self, email: str) -> bool:
        """Comprueba si ya existe un usuario con ese email."""
        return self.get_by_email(email) is not None
