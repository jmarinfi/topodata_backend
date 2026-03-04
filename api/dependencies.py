from typing import Annotated

from fastapi import Depends

from data.database import SessionDep
from data.repositories import (
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    ProjectRepository,
    RawObservationRepository,
    ReferenceCoordinateRepository,
    StationSetupRepository,
)
from services import (
    ApproximateCoordinateService,
    BesselObservationService,
    ImportSessionService,
    ProjectService,
    RawObservationService,
    ReferenceCoordinateService,
    StationSetupService,
)


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


def get_raw_observation_repository(db: SessionDep) -> RawObservationRepository:
    return RawObservationRepository(session=db)


RawObservationRepositoryDep = Annotated[
    RawObservationRepository, Depends(get_raw_observation_repository)
]


def get_raw_observation_service(
    repo: RawObservationRepositoryDep, station_setup_repo: StationSetupRepositoryDep
) -> RawObservationService:
    return RawObservationService(
        repository=repo, repository_station_setup=station_setup_repo
    )


RawObservationServiceDep = Annotated[
    RawObservationService, Depends(get_raw_observation_service)
]


def get_bessel_observation_repository(db: SessionDep) -> BesselObservationRepository:
    return BesselObservationRepository(session=db)


BesselObservationRepositoryDep = Annotated[
    BesselObservationRepository, Depends(get_bessel_observation_repository)
]


def get_bessel_observation_service(
    repo: BesselObservationRepositoryDep, station_setup_repo: StationSetupRepositoryDep
) -> BesselObservationService:
    return BesselObservationService(
        repository=repo, repository_station_setup=station_setup_repo
    )


BesselObservationServiceDep = Annotated[
    BesselObservationService, Depends(get_bessel_observation_service)
]


def get_reference_coordinate_repository(
    db: SessionDep,
) -> ReferenceCoordinateRepository:
    return ReferenceCoordinateRepository(session=db)


ReferenceCoordinateRepositoryDep = Annotated[
    ReferenceCoordinateRepository, Depends(get_reference_coordinate_repository)
]


def get_reference_coordinate_service(
    repo: ReferenceCoordinateRepositoryDep, project_repo: ProjectRepositoryDep
):
    return ReferenceCoordinateService(repository=repo, repository_project=project_repo)


ReferenceCoordinateServiceDep = Annotated[
    ReferenceCoordinateService, Depends(get_reference_coordinate_service)
]


def get_approximate_coordinate_repository(
    db: SessionDep,
) -> ApproximateCoordinateRepository:
    return ApproximateCoordinateRepository(session=db)


ApproximateCoordinateRepositoryDep = Annotated[
    ApproximateCoordinateRepository, Depends(get_approximate_coordinate_repository)
]


def get_approximate_coordinate_service(
    repo: ApproximateCoordinateRepositoryDep,
    bessel_observation_repo: BesselObservationRepositoryDep,
) -> ApproximateCoordinateService:
    return ApproximateCoordinateService(
        repository=repo, repository_bessel_observation=bessel_observation_repo
    )


ApproximateCoordinateServiceDep = Annotated[
    ApproximateCoordinateService, Depends(get_approximate_coordinate_service)
]
