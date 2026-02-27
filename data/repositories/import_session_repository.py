from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import ImportSession
from data.repositories.base_repository import BaseRepository


class ImportSessionRepository(BaseRepository):
    """Repositorio para las sesiones de importación."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=ImportSession, session=session)

    def get_by_project(self, project_id: int) -> Sequence[ImportSession]:
        result = self._session.execute(
            select(ImportSession).where(ImportSession.project_id == project_id)
        )
        return result.scalars().all()
