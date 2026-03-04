from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import ApproximateCoordinate
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
