from api.schemas import StationSetupCreate, StationSetupResponse, StationSetupUpdate
from data.repositories import ImportSessionRepository, StationSetupRepository


class StationSetupService:
    """Servicio para la gestión de estacionamientos."""

    def __init__(
        self,
        repository: StationSetupRepository,
        repository_import_session: ImportSessionRepository,
    ) -> None:
        self.repository = repository
        self.repository_import_session = repository_import_session

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

    def delete_station_setup(self, station_setup_id: int) -> None:
        db_station_setup = self.repository.get(station_setup_id)
        if not db_station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )
        self.repository.delete(db_station_setup)
