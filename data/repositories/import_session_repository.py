from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database.models import ImportSession
from data.repositories.base_repository import BaseRepository


class ImportSessionRepository(BaseRepository[ImportSession]):
    """Repositorio para las sesiones de importación."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=ImportSession, session=session)

    def get_by_project(self, project_id: int) -> Sequence[ImportSession]:
        return self._session.scalars(
            select(ImportSession).where(ImportSession.project_id == project_id)
        ).all()

    def get_by_project_and_hash(
        self, project_id: int, content_hash: str
    ) -> ImportSession | None:
        return self._session.scalars(
            select(ImportSession).where(
                ImportSession.project_id == project_id,
                ImportSession.content_hash == content_hash,
            )
        ).one_or_none()
