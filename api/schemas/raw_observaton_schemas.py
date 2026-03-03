from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RawObservationBase(BaseModel):
    """Esquema base para las observaciones brutas."""

    station_setup_id: int = Field(..., description="Id del estacionamiento")
    target_name: str = Field(..., max_length=255, description="Nombre del objetivo")
    target_number: int = Field(..., description="Número del objetivo")
    circle: int = Field(..., ge=1, le=2, description="Número de círculo")
    hz_angle: float = Field(..., description="Ángulo horizontal")
    v_angle: float = Field(..., description="Ángulo vertical")
    distance_geom: float = Field(..., description="Distancia geométrica")
    gis_prism_id: int | None = Field(None, description="Id del prisma en el GIS")
    observation_time: datetime | None = Field(
        None, description="Fecha y hora de la observación"
    )
    prism_constant: float | None = Field(None, description="Constante del prisma")
    target_height: float | None = Field(None, description="Altura del objetivo")
    temperature: float | None = Field(None, description="Temperatura")
    pressure: float | None = Field(None, description="Presión")
    refraction_coef: float | None = Field(None, description="Coeficiente de refracción")
    std_dev_hz: float | None = Field(None, description="Desviación estándar horizontal")
    std_dev_v: float | None = Field(None, description="Desviación estándar vertical")
    std_dev_dist: float | None = Field(
        None, description="Desviación estándar de distancia"
    )


class RawObservationCreate(RawObservationBase):
    """Esquema para crear observaciones brutas."""

    ...


class RawObservationUpdate(RawObservationBase):
    """Esquema para actualizar observaciones brutas."""

    ...


class RawObservationResponse(RawObservationBase):
    """Esquema para obtener observaciones brutas de la base de datos."""

    id: int = Field(..., description="Id de la observación")

    model_config = ConfigDict(from_attributes=True)
