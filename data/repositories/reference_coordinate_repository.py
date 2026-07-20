from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from data.database.models import Coordinate, ReferenceCoordinate
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

    def delete_by_project(self, project_id: int) -> None:
        """Borra en bloque las coordenadas de referencia de un proyecto.

        Con la herencia joined-table, un ``delete()`` bulk sobre
        ``reference_coordinates`` no borra la fila padre en ``coordinates``;
        hay que hacerlo a mano para no dejar coordenadas huérfanas.
        """
        ref_ids = select(ReferenceCoordinate.id).where(
            ReferenceCoordinate.project_id == project_id
        )
        self._session.execute(delete(Coordinate).where(Coordinate.id.in_(ref_ids)))
        self._session.execute(
            delete(ReferenceCoordinate).where(
                ReferenceCoordinate.project_id == project_id
            )
        )
        self._session.flush()
