from sqlalchemy.orm import Session

from data.database.models import Project
from data.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repositorio de los proyectos."""

    def __init__(self, session: Session) -> None:
        super().__init__(model=Project, session=session)
