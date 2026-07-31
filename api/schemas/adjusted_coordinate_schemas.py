from typing import Literal

from pydantic import ConfigDict, Field

from api.schemas.coordinate_schemas import CoordinateBase


class AdjustedCoordinateBase(CoordinateBase):
    bessel_observation_id: int = Field(
        ..., description="Id de la observación de Bessel"
    )
    prec_x: float = Field(..., description="Precisión ajustada en X")
    prec_y: float = Field(..., description="Precisión ajustada en Y")


class AdjustedCoordinateCreate(AdjustedCoordinateBase):
    ...


class AdjustedCoordinateResponse(AdjustedCoordinateBase):
    id: int = Field(..., description="Id de la coordenada ajustada")
    type: Literal["adjusted"] = Field(
        default="adjusted", description="Tipo de coordenada"
    )

    model_config = ConfigDict(from_attributes=True)
