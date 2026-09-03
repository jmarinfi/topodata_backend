from api.schemas import StationSetupCreate, StationSetupResponse, StationSetupUpdate
from data.repositories import (
    AdjustedCoordinateRepository,
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    RawObservationRepository,
    StationSetupRepository,
)


class StationSetupService:
    """Servicio para la gestión de estacionamientos."""

    def __init__(
        self,
        repository: StationSetupRepository,
        repository_import_session: ImportSessionRepository,
        repository_raw_observation: RawObservationRepository,
        repository_bessel_observation: BesselObservationRepository,
        repository_approximate_coordinate: ApproximateCoordinateRepository,
        repository_adjusted_coordinate: AdjustedCoordinateRepository,
    ) -> None:
        self.repository = repository
        self.repository_import_session = repository_import_session
        self.repository_raw_observation = repository_raw_observation
        self.repository_bessel_observation = repository_bessel_observation
        self.repository_approximate_coordinate = repository_approximate_coordinate
        self.repository_adjusted_coordinate = repository_adjusted_coordinate

    def get_station_setups(self) -> list[StationSetupResponse]:
        stations_setups = self.repository.get_all()
        return [
            StationSetupResponse.model_validate(station_setup)
            for station_setup in stations_setups
        ]

    def get_station_setups_by_import_session(
        self, import_session_id: int
    ) -> list[StationSetupResponse]:
        station_setups = self.repository.get_by_import_session(import_session_id)
        return [
            StationSetupResponse.model_validate(station_setup)
            for station_setup in station_setups
        ]

    def get_station_setup(self, station_setup_id: int) -> StationSetupResponse:
        station_setup = self.repository.get(station_setup_id)
        if not station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )
        return StationSetupResponse.model_validate(station_setup)

    def get_number_station_setups(self) -> int:
        return self.repository.count()

    def create_station_setup(
        self, station_setup_data: StationSetupCreate
    ) -> StationSetupResponse:
        import_session = self.repository_import_session.get(
            station_setup_data.import_session_id
        )
        if not import_session:
            raise ValueError(
                f"Sesión de importación con id {station_setup_data.import_session_id} no encontrada."
            )

        attributes = station_setup_data.model_dump()
        station_setup = self.repository.create(attributes)
        self.repository.refresh(station_setup)
        return StationSetupResponse.model_validate(station_setup)

    def update_station_setup(
        self, station_setup_id: int, station_setup_data: StationSetupUpdate
    ) -> StationSetupResponse:
        db_station_setup = self.repository.get(station_setup_id)
        if not db_station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )

        attributes = station_setup_data.model_dump()
        station_setup = self.repository.update(db_station_setup, attributes)
        self.repository.refresh(station_setup)
        return StationSetupResponse.model_validate(station_setup)

    def _delete_station_setup_children(self, station_setup_id: int) -> None:
        """Borra en bloque las coordenadas ajustadas y aproximadas y las
        observaciones Bessel y brutas vinculadas a un estacionamiento (sin
        tocar el propio estacionamiento).

        Punto único de verdad de la cascada hacia abajo: si en el futuro se
        añade una nueva entidad hija de ``station_setup``, este es el único
        método que hay que tocar. El borrado es por sentencia bulk (una por
        tabla) en vez de fila a fila para evitar un N+1 en sesiones grandes.
        """
        # Orden: primero las coordenadas (ajustadas y aproximadas), cuyos
        # deletes localizan sus filas con un subselect sobre
        # ``bessel_observations`` — necesitan que esas filas aún existan.
        # Ambos borran también la fila padre en ``coordinates`` (herencia
        # joined-table). Después las Bessel y por último las brutas.
        self.repository_adjusted_coordinate.delete_by_station_setup(station_setup_id)
        self.repository_approximate_coordinate.delete_by_station_setup(station_setup_id)
        self.repository_bessel_observation.delete_by_station_setup(station_setup_id)
        self.repository_raw_observation.delete_by_station_setup(station_setup_id)

    def delete_station_setup(self, station_setup_id: int) -> None:
        db_station_setup = self.repository.get(station_setup_id)
        if not db_station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )

        self._delete_station_setup_children(station_setup_id)
        self.repository.delete(db_station_setup)
