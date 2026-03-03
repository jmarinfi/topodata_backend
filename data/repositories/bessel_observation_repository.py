from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import BesselObservation
from data.repositories.base_repository import BaseRepository


class BesselObservationRepository(BaseRepository[BesselObservation]):
    """Repositorio para las observaciones de Bessel."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=BesselObservation, session=session)

    def get_by_station_setup(
        self, station_setup_id: int
    ) -> Sequence[BesselObservation]:
        return self._session.scalars(
            select(BesselObservation).where(
                BesselObservation.station_setup_id == station_setup_id
            )
        ).all()
