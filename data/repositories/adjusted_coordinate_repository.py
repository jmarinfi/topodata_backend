from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from data.database.models import AdjustedCoordinate, BesselObservation, Coordinate
from data.repositories.base_repository import BaseRepository


class AdjustedCoordinateRepository(BaseRepository[AdjustedCoordinate]):
    def __init__(self, session: Session) -> None:
        super().__init__(model=AdjustedCoordinate, session=session)

    def get_by_bessel_observation(
        self, bessel_observation_id: int
    ) -> AdjustedCoordinate | None:
        return self._session.scalars(
            select(AdjustedCoordinate).where(
                AdjustedCoordinate.bessel_observation_id == bessel_observation_id
            )
        ).one_or_none()

    def get_by_station_setup(
        self, station_setup_id: int
    ) -> list[AdjustedCoordinate]:
        bessel_ids = select(BesselObservation.id).where(
            BesselObservation.station_setup_id == station_setup_id
        )
        return list(
            self._session.scalars(
                select(AdjustedCoordinate).where(
                    AdjustedCoordinate.bessel_observation_id.in_(bessel_ids)
                )
            ).all()
        )

    def delete_by_station_setup(self, station_setup_id: int) -> None:
        bessel_ids = select(BesselObservation.id).where(
            BesselObservation.station_setup_id == station_setup_id
        )
        adjusted_ids = select(AdjustedCoordinate.id).where(
            AdjustedCoordinate.bessel_observation_id.in_(bessel_ids)
        )
        self._session.execute(delete(Coordinate).where(Coordinate.id.in_(adjusted_ids)))
        self._session.execute(
            delete(AdjustedCoordinate).where(
                AdjustedCoordinate.bessel_observation_id.in_(bessel_ids)
            )
        )
        self._session.flush()
