from typing import Annotated

from fastapi import Depends

from data.database import SessionDep
from data.repositories import (
    ImportSessionRepository,
    ProjectRepository,
    StationSetupRepository,
)
from services import ImportSessionService, ProjectService, StationSetupService


def get_project_repository(db: SessionDep) -> ProjectRepository:
    return ProjectRepository(session=db)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_project_service(repo: ProjectRepositoryDep) -> ProjectService:
    return ProjectService(repository=repo)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_import_session_repository(db: SessionDep) -> ImportSessionRepository:
    return ImportSessionRepository(session=db)


ImportSessionRepositoryDep = Annotated[
    ImportSessionRepository, Depends(get_import_session_repository)
]


def get_import_session_service(
    repo: ImportSessionRepositoryDep, project_repo: ProjectRepositoryDep
) -> ImportSessionService:
    return ImportSessionService(repository=repo, repository_project=project_repo)


ImportSessionServiceDep = Annotated[
    ImportSessionService, Depends(get_import_session_service)
]


def get_station_setup_repository(db: SessionDep) -> StationSetupRepository:
    return StationSetupRepository(session=db)


StationSetupRepositoryDep = Annotated[
    StationSetupRepository, Depends(get_station_setup_repository)
]


def get_station_setup_service(
    repo: StationSetupRepositoryDep, import_session_repo: ImportSessionRepositoryDep
) -> StationSetupService:
    return StationSetupService(
        repository=repo, repository_import_session=import_session_repo
    )


StationSetupServiceDep = Annotated[
    StationSetupService, Depends(get_station_setup_service)
]
