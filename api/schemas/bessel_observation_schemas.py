from pydantic import BaseModel, ConfigDict, Field


class BesselObservationBase(BaseModel):
    """Esquema base para las observaciones Bessel."""

    station_setup_id: int = Field(..., description="Id del estacionamiento")
    target_name: str = Field(..., max_length=255, description="Nombre del objetivo")
    hz_angle_direct: float = Field(..., description="Angulo horizontal directo")
    v_angle_direct: float = Field(..., description="Angulo vertical directo")
    distance_direct: float = Field(..., description="Distancia directa")
    hz_angle_inverse: float = Field(..., description="Angulo horizontal inverso")
    v_angle_inverse: float = Field(..., description="Angulo vertical inverso")
    distance_inverse: float = Field(..., description="Distancia inversa")
    hz_angle_bessel: float = Field(..., description="Angulo horizontal Bessel")
    v_angle_bessel: float = Field(..., description="Angulo vertical Bessel")
    distance_bessel: float = Field(..., description="Distancia Bessel")
    hz_angle_delta: float = Field(..., description="Angulo horizontal delta")
    v_angle_delta: float = Field(..., description="Angulo vertical delta")
    distance_delta: float = Field(..., description="Distancia delta")


class BesselObservationCreate(BesselObservationBase):
    """Esquema para crear observaciones Bessel."""

    ...


class BesselObservationUpdate(BesselObservationBase):
    """Esquema para actualizar observaciones Bessel."""

    ...


class BesselObservationResponse(BesselObservationBase):
    """Esquema para obtener observaciones Bessel de la base de datos."""

    id: int = Field(..., description="Id de la observación")

    model_config = ConfigDict(from_attributes=True)
