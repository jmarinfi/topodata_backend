from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # JWT
    secret_key: str = Field(..., description="Clave secreta para firmar los tokens JWT")
    algorithm: str = Field(default="HS256", description="Algoritmo de firma JWT")
    access_token_expire_minutes: int = Field(
        default=60, description="Duración del token en minutos"
    )


settings = Settings()  # type: ignore[call-arg]
