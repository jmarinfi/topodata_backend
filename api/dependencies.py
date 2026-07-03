from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from api.schemas.user_schemas import UserResponse
from data.database import SessionDep
from data.repositories import (
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    ProjectRepository,
    RawObservationRepository,
    ReferenceCoordinateRepository,
    StationSetupRepository,
    UserRepository,
)
from services import (
    ApproximateCoordinateService,
    BesselObservationService,
    ImportOrchestratorService,
    ImportSessionService,
    PasswordService,
    ProjectService,
    RawObservationService,
    ReferenceCoordinateService,
    StationSetupService,
    TokenService,
    UserService,
)

# --- Projects ---


def get_project_repository(db: SessionDep) -> ProjectRepository:
    return ProjectRepository(session=db)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_project_service(
    repo: ProjectRepositoryDep, import_session_repo: ImportSessionRepositoryDep
) -> ProjectService:
    return ProjectService(
        repository=repo, repository_import_session=import_session_repo
    )


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


# --- Import Sessions ---


def get_import_session_repository(db: SessionDep) -> ImportSessionRepository:
    return ImportSessionRepository(session=db)


ImportSessionRepositoryDep = Annotated[
    ImportSessionRepository, Depends(get_import_session_repository)
]


def get_import_session_service(
    repo: ImportSessionRepositoryDep,
    project_repo: ProjectRepositoryDep,
    station_setup_repo: StationSetupRepositoryDep,
) -> ImportSessionService:
    return ImportSessionService(
        repository=repo,
        repository_project=project_repo,
        repository_station_setup=station_setup_repo,
    )


ImportSessionServiceDep = Annotated[
    ImportSessionService, Depends(get_import_session_service)
]


# --- Station Setups ---


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


# --- Raw Observations ---


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


# --- Bessel Observations ---


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


# --- Reference Coordinates ---


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


# --- Approximate coordinates ---


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


# --- Import Orchestrator ---


def get_import_orchestrator_service(
    import_repo: ImportSessionRepositoryDep,
    station_repo: StationSetupRepositoryDep,
    obs_repo: RawObservationRepositoryDep,
) -> ImportOrchestratorService:
    return ImportOrchestratorService(
        import_repo=import_repo, station_repo=station_repo, obs_repo=obs_repo
    )


ImportOrchestratorServiceDep = Annotated[
    ImportOrchestratorService, Depends(get_import_orchestrator_service)
]


# --- Auth / Users ---


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

OAuth2Dep = Annotated[str, Depends(oauth2_scheme)]


def get_user_repository(db: SessionDep) -> UserRepository:
    return UserRepository(session=db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_password_service() -> PasswordService:
    return PasswordService()


def get_token_service() -> TokenService:
    return TokenService()


def get_user_service(
    repo: UserRepositoryDep,
    password_service: Annotated[PasswordService, Depends(get_password_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> UserService:
    return UserService(
        repository=repo, password_service=password_service, token_service=token_service
    )


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_current_user(token: OAuth2Dep, service: UserServiceDep) -> UserResponse:
    try:
        token_svc = TokenService()
        payload = token_svc.decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )

    user = service.repository.get(payload.sub)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada.")

    return UserResponse.model_validate(user)


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
