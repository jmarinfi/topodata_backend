from typing import Annotated

from fastapi import Depends

from data.database import SessionDep
from data.repositories import ProjectRepository
from services import ProjectService


def get_project_repository(db: SessionDep) -> ProjectRepository:
    return ProjectRepository(session=db)


def get_project_service(
    repo: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ProjectService:
    return ProjectService(repository=repo)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
