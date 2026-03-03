from api.schemas import (
    BesselObservationCreate,
    BesselObservationResponse,
    BesselObservationUpdate,
)
from data.repositories import BesselObservationRepository, StationSetupRepository


class BesselObservationService:
    """Servicio para la gestión de observaciones Bessel."""

    def __init__(
        self,
        repository: BesselObservationRepository,
        repository_station_setup: StationSetupRepository,
    ) -> None:
        self.repository = repository
        self.repository_station_setup = repository_station_setup

    def get_bessel_observations(self) -> list[BesselObservationResponse]:
        bessel_observations = self.repository.get_all()
        return [
            BesselObservationResponse.model_validate(bessel_observation)
            for bessel_observation in bessel_observations
        ]

    def get_bessel_observations_by_station_setup(
        self, station_setup_id: int
    ) -> list[BesselObservationResponse]:
        bessel_observations = self.repository.get_by_station_setup(station_setup_id)
        return [
            BesselObservationResponse.model_validate(bessel_observation)
            for bessel_observation in bessel_observations
        ]

    def get_bessel_observation(
        self, bessel_observation_id: int
    ) -> BesselObservationResponse:
        bessel_observation = self.repository.get(bessel_observation_id)
        if not bessel_observation:
            raise ValueError(
                f"Observación Bessel con id {bessel_observation_id} no encontrada."
            )
        return BesselObservationResponse.model_validate(bessel_observation)

    def get_number_bessel_observations(self) -> int:
        return self.repository.count()

    def create_bessel_observation(
        self, bessel_observation_data: BesselObservationCreate
    ) -> BesselObservationResponse:
        station_setup = self.repository_station_setup.get(
            bessel_observation_data.station_setup_id
        )
        if not station_setup:
            raise ValueError(
                f"Estacionamiento con id {bessel_observation_data.station_setup_id} no encontrado."
            )

        attributes = bessel_observation_data.model_dump()
        bessel_observation = self.repository.create(attributes)
        self.repository.refresh(bessel_observation)
        return BesselObservationResponse.model_validate(bessel_observation)

    def update_bessel_observation(
        self,
        bessel_observation_id: int,
        bessel_observation_data: BesselObservationUpdate,
    ) -> BesselObservationResponse:
        db_bessel_observation = self.repository.get(bessel_observation_id)
        if not db_bessel_observation:
            raise ValueError(
                f"Observación Bessel con id {bessel_observation_id} no encontrada."
            )

        attributes = bessel_observation_data.model_dump()
        bessel_observation = self.repository.update(db_bessel_observation, attributes)
        self.repository.refresh(bessel_observation)
        return BesselObservationResponse.model_validate(bessel_observation)

    def delete_bessel_observation(self, bessel_observation_id: int) -> None:
        db_bessel_observation = self.repository.get(bessel_observation_id)
        if not db_bessel_observation:
            raise ValueError(
                f"Observación Bessel con id {bessel_observation_id} no encontrada."
            )
        self.repository.delete(db_bessel_observation)
