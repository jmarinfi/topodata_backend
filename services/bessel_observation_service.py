import logging
from dataclasses import dataclass

from api.schemas import (
    BesselObservationCreate,
    BesselObservationResponse,
    BesselObservationUpdate,
    RawObservationResponse,
    StationSetupResponse,
)
from data.repositories import (
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    RawObservationRepository,
    StationSetupRepository,
)
from services.calculations.bessel_adjuster import BesselAdjuster

logger = logging.getLogger(__name__)


@dataclass
class BesselCalculationResult:
    """Resultado de calcular Bessel para un estacionamiento.

    ``warning`` se rellena cuando el cálculo se omite (estación sin
    observaciones brutas o sin pares directo/inverso válidos); en ese caso
    ``bessel_observations`` viene vacía. El orquestador propaga estos
    warnings al ``GkaImportResult`` para que el llamante los vea.
    """

    bessel_observations: list[BesselObservationResponse]
    warning: str | None = None


class BesselObservationService:
    """Servicio para la gestión de observaciones Bessel."""

    def __init__(
        self,
        repository: BesselObservationRepository,
        repository_station_setup: StationSetupRepository,
        repository_raw_observation: RawObservationRepository,
        repository_approximate_coordinate: ApproximateCoordinateRepository,
    ) -> None:
        self.repository = repository
        self.repository_station_setup = repository_station_setup
        self.repository_raw_observation = repository_raw_observation
        self.repository_approximate_coordinate = repository_approximate_coordinate

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

    def calculate_for_station_setup(
        self, station_setup_id: int
    ) -> BesselCalculationResult:
        """Calcula y persiste las observaciones Bessel de un estacionamiento.

        Toma las ``RawObservation`` del estacionamiento, las pasa por
        ``BesselAdjuster`` y reemplaza cualquier ``BesselObservation`` previa
        (y las ``ApproximateCoordinate`` derivadas) por las recién calculadas.
        Es idempotente: si se llama dos veces, el resultado es el mismo.

        Política de fallo suave: si el estacionamiento no tiene
        observaciones brutas o el adjuster no encuentra pares
        directo/inverso válidos, no se modifica nada y se devuelve un
        ``BesselCalculationResult`` con ``bessel_observations=[]`` y
        ``warning`` con la razón. Solo se lanza ``ValueError`` si el
        estacionamiento no existe.

        Returns:
            ``BesselCalculationResult`` con las observaciones persistidas y,
            si el cálculo se omitió, el motivo en ``warning``.
        """
        station_setup = self.repository_station_setup.get(station_setup_id)
        if not station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )

        raw_observations = self.repository_raw_observation.get_by_station_setup(
            station_setup_id
        )
        if not raw_observations:
            msg = (
                f"Estacionamiento {station_setup_id} "
                f"({station_setup.station_name}): sin observaciones brutas, "
                f"Bessel omitido."
            )
            logger.warning(msg)
            return BesselCalculationResult(bessel_observations=[], warning=msg)

        station_response = StationSetupResponse.model_validate(station_setup)
        raw_responses = [
            RawObservationResponse.model_validate(o) for o in raw_observations
        ]

        try:
            new_observations: list[BesselObservationCreate] = BesselAdjuster(
                station_setup=station_response, raw_observations=raw_responses
            ).adjust_bessel()
        except ValueError as e:
            # El adjuster lanza ValueError cuando no hay pares directo/inverso
            # válidos. Por política de import, omitimos y seguimos: la
            # importación no debe abortarse por un estacionamiento con datos
            # incompletos.
            msg = (
                f"Estacionamiento {station_setup_id} "
                f"({station_setup.station_name}): sin pares directo/inverso "
                f"válidos, Bessel omitido ({e})."
            )
            logger.warning(msg)
            return BesselCalculationResult(bessel_observations=[], warning=msg)

        # Idempotencia: cascade hacia abajo (approx -> bessel), mismo orden
        # que StationSetupService._delete_station_setup_children.
        self.repository_approximate_coordinate.delete_by_station_setup(
            station_setup_id
        )
        self.repository.delete_by_station_setup(station_setup_id)

        persisted: list[BesselObservationResponse] = []
        for obs_in in new_observations:
            attributes = obs_in.model_dump()
            obs = self.repository.create(attributes)
            self.repository.refresh(obs)
            persisted.append(BesselObservationResponse.model_validate(obs))

        return BesselCalculationResult(bessel_observations=persisted)
