from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StationSetupBase(BaseModel):
    """Esquema base para los estacionamientos."""

    import_session_id: int = Field(..., description="Id de la sesión de importación")
    station_name: str = Field(
        ..., max_length=255, description="Nombre del estacionamiento"
    )
    station_height: float | None = Field(None, description="Altura del estacionamiento")
    edm_refractive_index: float | None = Field(
        None, description="Índice de refracción EDM"
    )
    edm_carrier_wavelength: float | None = Field(
        None, description="Longitud de onda del carril EDM"
    )
    start_time: datetime | None = Field(
        None, description="Hora de inicio del estacionamiento"
    )
    end_time: datetime | None = Field(
        None, description="Hora de finalización del estacionamiento"
    )
    description: str | None = Field(None, description="Descripción del estacionamiento")


class StationSetupCreate(StationSetupBase):
    """Esquema para crear estacionamientos."""

    ...


class StationSetupUpdate(StationSetupBase):
    """Esquema para actualizar estacionamientos."""

    etr_x: float | None = Field(None, description="Coordenada X del estacionamiento")
    etr_y: float | None = Field(None, description="Coordenada Y del estacionamiento")
    etr_z: float | None = Field(None, description="Coordenada Z del estacionamiento")
    k_utm: float | None = Field(None, description="Factor de escala UTM")
    desorientacion: float | None = Field(
        None, description="Desorientación del estacionamiento"
    )


class StationSetupResponse(StationSetupBase):
    """Esquema para obtener estacionamientos de la base de datos."""

    id: int = Field(..., description="Id del estacionamiento")
    etr_x: float | None = Field(None, description="Coordenada X del estacionamiento")
    etr_y: float | None = Field(None, description="Coordenada Y del estacionamiento")
    etr_z: float | None = Field(None, description="Coordenada Z del estacionamiento")
    k_utm: float | None = Field(None, description="Factor de escala UTM")
    desorientacion: float | None = Field(
        None, description="Desorientación del estacionamiento"
    )

    model_config = ConfigDict(from_attributes=True)
