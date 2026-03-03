from api.schemas import (
    RawObservationCreate,
    RawObservationResponse,
    RawObservationUpdate,
)
from data.repositories import RawObservationRepository, StationSetupRepository


class RawObservationService:
    """Servicio para la gestión de observaciones."""

    def __init__(
        self,
        repository: RawObservationRepository,
        repository_station_setup: StationSetupRepository,
    ) -> None:
        self.repository = repository
        self.repository_station_setup = repository_station_setup

    def get_raw_observations(self) -> list[RawObservationResponse]:
        raw_observations = self.repository.get_all()
        return [
            RawObservationResponse.model_validate(raw_observation)
            for raw_observation in raw_observations
        ]

    def get_raw_observations_by_station_setup(
        self, station_setup_id: int
    ) -> list[RawObservationResponse]:
        raw_observations = self.repository.get_by_station_setup(station_setup_id)
        return [
            RawObservationResponse.model_validate(raw_observation)
            for raw_observation in raw_observations
        ]

    def get_raw_observation(self, raw_observation_id: int) -> RawObservationResponse:
        raw_observation = self.repository.get(raw_observation_id)
        if not raw_observation:
            raise ValueError(f"Observación con id {raw_observation_id} no encontrada.")
        return RawObservationResponse.model_validate(raw_observation)

    def get_number_raw_observations(self) -> int:
        return self.repository.count()

    def create_raw_observation(
        self, raw_observation_data: RawObservationCreate
    ) -> RawObservationResponse:
        station_setup = self.repository_station_setup.get(
            raw_observation_data.station_setup_id
        )
        if not station_setup:
            raise ValueError(
                f"Estacionamiento con id {raw_observation_data.station_setup_id} no encontrado."
            )

        attributes = raw_observation_data.model_dump()
        raw_observation = self.repository.create(attributes)
        self.repository.refresh(raw_observation)
        return RawObservationResponse.model_validate(raw_observation)

    def update_raw_observation(
        self, raw_observation_id: int, raw_observation_data: RawObservationUpdate
    ) -> RawObservationResponse:
        db_raw_observation = self.repository.get(raw_observation_id)
        if not db_raw_observation:
            raise ValueError(f"Observación con id {raw_observation_id} no encontrada.")

        attributes = raw_observation_data.model_dump()
        raw_observation = self.repository.update(db_raw_observation, attributes)
        self.repository.refresh(raw_observation)
        return RawObservationResponse.model_validate(raw_observation)

    def delete_raw_observation(self, raw_observation_id: int) -> None:
        db_raw_observation = self.repository.get(raw_observation_id)
        if not db_raw_observation:
            raise ValueError(f"Observación con id {raw_observation_id} no encontrada.")
        self.repository.delete(db_raw_observation)
