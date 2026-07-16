from pydantic import BaseModel, ConfigDict, Field

from api.schemas.import_session_schemas import ImportSessionResponse
from api.schemas.raw_observaton_schemas import RawObservationResponse
from api.schemas.station_setup_schemas import StationSetupResponse


class GkaImportResult(BaseModel):
    """Esquema para el resultado completo de la importación GKA."""

    import_session: ImportSessionResponse
    station_setups: list[StationSetupResponse]
    raw_observations: list[RawObservationResponse]
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Avisos no bloqueantes surgidos durante la importación "
            "(p.ej. estacionamientos sin pares directo/inverso válidos "
            "para Bessel)."
        ),
    )

    model_config = ConfigDict(from_attributes=True)
