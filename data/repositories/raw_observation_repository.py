from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import RawObservation
from data.repositories.base_repository import BaseRepository


class RawObservationRepository(BaseRepository[RawObservation]):
    """Repositorio para las observaciones brutas."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=RawObservation, session=session)

    def get_by_station_setup(self, station_setup_id: int) -> Sequence[RawObservation]:
        return self._session.scalars(
            select(RawObservation).where(
                RawObservation.station_setup_id == station_setup_id
            )
        ).all()
