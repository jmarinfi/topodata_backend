from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Esquema base para usuarios."""

    username: str = Field(
        ..., min_length=3, max_length=100, description="Nombre de usuario"
    )
    email: EmailStr = Field(..., description="Correo electrónico")


class UserCreate(UserBase):
    """Esquema para registrar un nuevo usuario."""

    password: str = Field(..., min_length=8, description="Contraseña en texto plano")


class UserUpdate(BaseModel):
    """Esquema para actualizar datos del usuario (PATCH parcial)."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Esquema de respuesta - nunca expone la contraseña."""

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de autenticación ---


class LoginRequest(BaseModel):
    """Credenciales para iniciar sesión."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token JWT devuelto tras un login exitoso."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload decodificado del token JWT."""

    sub: int  # user id
    username: str
    exp: datetime
