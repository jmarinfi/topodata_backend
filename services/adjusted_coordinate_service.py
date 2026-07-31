from api.schemas.adjusted_coordinate_schemas import AdjustedCoordinateResponse
from data.repositories.adjusted_coordinate_repository import (
    AdjustedCoordinateRepository,
)
from data.repositories.station_setup_repository import StationSetupRepository


class AdjustedCoordinateService:
    def __init__(
        self,
        repository: AdjustedCoordinateRepository,
        repository_station_setup: StationSetupRepository,
    ) -> None:
        self.repository = repository
        self.repository_station_setup = repository_station_setup

    def get_all(self) -> list[AdjustedCoordinateResponse]:
        return [
            AdjustedCoordinateResponse.model_validate(c)
            for c in self.repository.get_all()
        ]

    def get_by_station_setup(
        self, station_setup_id: int
    ) -> list[AdjustedCoordinateResponse]:
        self._check_station_setup(station_setup_id)
        return [
            AdjustedCoordinateResponse.model_validate(c)
            for c in self.repository.get_by_station_setup(station_setup_id)
        ]

    def get(self, adjusted_coordinate_id: int) -> AdjustedCoordinateResponse:
        coord = self.repository.get(adjusted_coordinate_id)
        if not coord:
            raise ValueError(
                f"Coordenada ajustada con id {adjusted_coordinate_id} no encontrada."
            )
        return AdjustedCoordinateResponse.model_validate(coord)

    def count(self) -> int:
        return self.repository.count()

    def _check_station_setup(self, station_setup_id: int) -> None:
        if not self.repository_station_setup.get(station_setup_id):
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )
