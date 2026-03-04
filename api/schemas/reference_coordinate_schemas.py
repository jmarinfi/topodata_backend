from typing import Literal

from pydantic import ConfigDict, Field

from api.schemas.coordinate_schemas import CoordinateBase


class ReferenceCoordinateBase(CoordinateBase):
    """Esquema base para coordenadas de referencia."""

    project_id: int = Field(..., description="Id del proyecto asociado")


class ReferenceCoordinateCreate(ReferenceCoordinateBase):
    """Esquema para crear coordenadas de referencia."""

    ...


class ReferenceCoordinateUpdate(ReferenceCoordinateBase):
    """Esquema para actualizar coordenadas de referencia."""

    ...


class ReferenceCoordinateResponse(ReferenceCoordinateBase):
    """Esquema para obtener coordenadas de referencia de la base de datos."""

    id: int = Field(..., description="Id de la coordenada")
    type: Literal["reference"] = Field(
        default="reference", description="Tipo de coordenada"
    )

    model_config = ConfigDict(from_attributes=True)
