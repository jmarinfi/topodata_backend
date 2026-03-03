from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import StationSetup
from data.repositories.base_repository import BaseRepository


class StationSetupRepository(BaseRepository[StationSetup]):
    """Repositorio para los estacionamientos."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=StationSetup, session=session)

    def get_by_import_session(self, import_session_id: int):
        return self._session.scalars(
            select(StationSetup).where(
                StationSetup.import_session_id == import_session_id
            )
        ).all()
