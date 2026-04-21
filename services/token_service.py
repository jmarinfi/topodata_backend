from datetime import datetime, timedelta, timezone

import jwt

from api.schemas import TokenPayload
from core.config import settings


class TokenService:
    """Servicio para generar y validar tokens JWT."""

    def __init__(self) -> None:
        self._secret_key = settings.secret_key
        self._algorithm = settings.algorithm
        self._expire_minutes = settings.access_token_expire_minutes

    def create_access_token(self, user_id: int, username: str) -> str:
        """Genera un token JWT firmado con el ID y username del usuario."""

        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {"sub": str(user_id), "username": username, "exp": expire}

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> TokenPayload:
        """Decodifica y valida un token JWT."""

        try:
            raw = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return TokenPayload(
                sub=int(raw["sub"]),
                username=raw["username"],
                exp=datetime.fromtimestamp(raw["exp"], tz=timezone.utc),
            )

        except jwt.ExpiredSignatureError as e:
            raise ValueError("El token ha expirado.") from e

        except jwt.InvalidTokenError as e:
            raise ValueError(f"Token inválido: {e!r}") from e
