from typing import Literal

from pydantic import ConfigDict, Field

from api.schemas.coordinate_schemas import CoordinateBase


class ApproximateCoordinateBase(CoordinateBase):
    """Esquema base para las coordenadas aproximadas."""

    bessel_observation_id: int = Field(
        ..., description="Id de la observación de Bessel"
    )


class ApproximateCoordinateCreate(ApproximateCoordinateBase):
    """Esquema para la creación de coordenadas aproximadas."""

    ...


class ApproximateCoordinateUpdate(ApproximateCoordinateBase):
    """Esquema para la actualización de coordenadas aproximadas."""

    ...


class ApproximateCoordinateResponse(ApproximateCoordinateBase):
    """Esquema para obtener coordenadas aproximadas de la base de datos."""

    id: int = Field(..., description="Id de la coordenada aproximada")
    type: Literal["approximate"] = Field(
        default="approximate", description="Tipo de coordenada"
    )

    model_config = ConfigDict(from_attributes=True)
