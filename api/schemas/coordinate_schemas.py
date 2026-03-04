from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CoordinateBase(BaseModel):
    """Esquema base genérico para coordenadas."""

    target_name: str = Field(..., max_length=255, description="Nombre de la coordenada")
    x: float = Field(..., description="Valor de la coordenada X")
    y: float = Field(..., description="Valor de la coordenada Y")
    z: float = Field(..., description="Valor de la coordenada Z")


class CoordinateCreate(CoordinateBase):
    """Esquema para crear coordenadas."""

    ...


class CoordinateUpdate(CoordinateBase):
    """Esquema para actualizar coordenadas."""

    ...


class CoordinateResponse(CoordinateBase):
    """Esquema para obtener coordenadas de la base de datos."""

    id: int = Field(..., description="Id de la coordenada")
    type: Literal["coordinate"] = Field(
        default="coordinate", description="Tipo de coordenada (discriminador)"
    )

    model_config = ConfigDict(from_attributes=True)
