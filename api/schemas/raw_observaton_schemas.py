from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RawObservationBase(BaseModel):
    """Esquema base para las observaciones brutas."""

    target_name: str = Field(..., max_length=255, description="Nombre del objetivo")
    target_number: int = Field(..., description="Número del objetivo")
    circle: int = Field(..., ge=1, le=2, description="Número de círculo")
    hz_angle: float = Field(..., description="Ángulo horizontal")
    v_angle: float = Field(..., description="Ángulo vertical")
    distance_geom: float = Field(..., description="Distancia geométrica")
    gis_prism_id: int | None = Field(
        default=None, description="Id del prisma en el GIS"
    )
    observation_time: datetime | None = Field(
        default=None, description="Fecha y hora de la observación"
    )
    prism_constant: float | None = Field(
        default=None, description="Constante del prisma"
    )
    target_height: float | None = Field(default=None, description="Altura del objetivo")
    temperature: float | None = Field(default=None, description="Temperatura")
    pressure: float | None = Field(default=None, description="Presión")
    refraction_coef: float | None = Field(
        default=None, description="Coeficiente de refracción"
    )
    std_dev_hz: float | None = Field(
        default=None, description="Desviación estándar horizontal"
    )
    std_dev_v: float | None = Field(
        default=None, description="Desviación estándar vertical"
    )
    std_dev_dist: float | None = Field(
        default=None, description="Desviación estándar de distancia"
    )


class RawObservationParsed(RawObservationBase):
    """Esquema para parsear observaciones brutas."""

    ...


class RawObservationCreate(RawObservationBase):
    """Esquema para crear observaciones brutas."""

    station_setup_id: int = Field(..., description="Id del estacionamiento")


class RawObservationUpdate(RawObservationCreate):
    """Esquema para actualizar observaciones brutas."""

    ...


class RawObservationResponse(RawObservationUpdate):
    """Esquema para obtener observaciones brutas de la base de datos."""

    id: int = Field(..., description="Id de la observación")

    model_config = ConfigDict(from_attributes=True)
