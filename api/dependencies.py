from typing import Annotated

from fastapi import Depends

from data.database import SessionDep
from data.repositories import ProjectRepository, ImportSessionRepository
from services import ProjectService, ImportSessionService


def get_project_repository(db: SessionDep) -> ProjectRepository:
    return ProjectRepository(session=db)


def get_project_service(
    repo: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ProjectService:
    return ProjectService(repository=repo)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_import_session_repository(db: SessionDep) -> ImportSessionRepository:
    return ImportSessionRepository(session=db)


def get_import_session_service(
    repo: Annotated[ImportSessionRepository, Depends(get_import_session_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ImportSessionService:
    return ImportSessionService(repository=repo, repository_project=project_repo)


ImportSessionRepositoryDep = Annotated[
    ImportSessionRepository, Depends(get_import_session_repository)
]
ImportSessionServiceDep = Annotated[
    ImportSessionService, Depends(get_import_session_service)
]
