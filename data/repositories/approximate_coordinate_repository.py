from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from data.database.models import ApproximateCoordinate, BesselObservation, Coordinate
from data.repositories.base_repository import BaseRepository


class ApproximateCoordinateRepository(BaseRepository[ApproximateCoordinate]):
    """Repositorio para las coordenadas aproximadas."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=ApproximateCoordinate, session=session)

    def get_by_bessel_observation(
        self, bessel_observation_id: int
    ) -> ApproximateCoordinate | None:
        return self._session.scalars(
            select(ApproximateCoordinate).where(
                ApproximateCoordinate.bessel_observation_id == bessel_observation_id
            )
        ).one_or_none()

    def get_by_station_setup(
        self, station_setup_id: int
    ) -> list[ApproximateCoordinate]:
        """Coordenadas aproximadas cuyas observaciones Bessel pertenecen al
        estacionamiento indicado."""
        bessel_ids = select(BesselObservation.id).where(
            BesselObservation.station_setup_id == station_setup_id
        )
        return list(
            self._session.scalars(
                select(ApproximateCoordinate).where(
                    ApproximateCoordinate.bessel_observation_id.in_(bessel_ids)
                )
            ).all()
        )

    def delete_by_station_setup(self, station_setup_id: int) -> None:
        """Borra en bloque las coordenadas aproximadas de un estacionamiento.

        Con la herencia joined-table, un ``delete()`` bulk sobre
        ``approximate_coordinates`` no borra la fila padre en ``coordinates``;
        hay que hacerlo a mano para no dejar coordenadas huérfanas.
        """
        bessel_ids = select(BesselObservation.id).where(
            BesselObservation.station_setup_id == station_setup_id
        )
        approx_ids = select(ApproximateCoordinate.id).where(
            ApproximateCoordinate.bessel_observation_id.in_(bessel_ids)
        )
        self._session.execute(delete(Coordinate).where(Coordinate.id.in_(approx_ids)))
        self._session.execute(
            delete(ApproximateCoordinate).where(
                ApproximateCoordinate.bessel_observation_id.in_(bessel_ids)
            )
        )
        self._session.flush()
