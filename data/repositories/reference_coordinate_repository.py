from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import ReferenceCoordinate
from data.repositories.base_repository import BaseRepository


class ReferenceCoordinateRepository(BaseRepository[ReferenceCoordinate]):
    """Repositorio para las coordenadas de referencia."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=ReferenceCoordinate, session=session)

    def get_by_project(self, project_id: int) -> Sequence[ReferenceCoordinate]:
        return self._session.scalars(
            select(ReferenceCoordinate).where(
                ReferenceCoordinate.project_id == project_id
            )
        ).all()
