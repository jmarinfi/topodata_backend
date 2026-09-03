"""Test de regresión — el borrado en cascada debe eliminar las coordenadas ajustadas.

Históricamente ``StationSetupService._delete_station_setup_children`` borraba
aproximadas, Bessel y brutas pero olvidaba las ``AdjustedCoordinate`` (y sus
filas padre en ``coordinates``); como SQLite no fuerza las FK, las huérfanas
se acumulaban sin error. Estos tests recorren la cascada real (proyecto →
sesión → estacionamiento) sobre datos que incluyen coordenadas ajustadas
creadas por el MMC y comprueban que no queda nada.

Flujo a nivel de servicio, mismo patrón que ``test_e2e_s01_recompute.py``:
proyecto + referencias → import GKA S01 (4 estacionamientos) → cálculo del
primero (aproximadas + ajustadas).
"""

from sqlalchemy import func, select

from data.database.models import (
    AdjustedCoordinate,
    ApproximateCoordinate,
    BesselObservation,
    Coordinate,
    ImportSession,
    Project,
    RawObservation,
    ReferenceCoordinate,
    StationSetup,
)
from data.repositories import (
    AdjustedCoordinateRepository,
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    ProjectRepository,
    RawObservationRepository,
    ReferenceCoordinateRepository,
    StationSetupRepository,
)
from services.bessel_observation_service import BesselObservationService
from services.import_orchestrator_service import ImportOrchestratorService
from services.import_session_service import ImportSessionService
from services.project_service import ProjectService
from services.reference_coordinate_service import ReferenceCoordinateService
from services.station_setup_service import StationSetupService
from services.approximate_coordinate_service import ApproximateCoordinateService
from tests.e2e_helpers import extract_reference_coords, read_gka

S01_GKA = "20251112_200023_20251112_210627.gka"

# Las 9 tablas que debe vaciar el borrado de un proyecto.
ALL_TABLES = (
    Project,
    ImportSession,
    StationSetup,
    RawObservation,
    BesselObservation,
    Coordinate,
    ApproximateCoordinate,
    AdjustedCoordinate,
    ReferenceCoordinate,
)


def _count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def _setup_project_with_adjusted(db) -> Project:
    """Crea el proyecto completo con coordenadas ajustadas (MMC) calculadas."""
    project_repo = ProjectRepository(db)
    project = project_repo.create(
        {
            "name": "Cascada de borrado",
            "coordinate_system": "EPSG:25830",
            "zona_utm": "30T",
            "a_elip": 6378137.0,
            "b_elip": 6356752.314,
            "f_elip": 1.0 / 298.257222101,
            "inv_f_elip": 298.257222101,
        }
    )

    ref_repo = ReferenceCoordinateRepository(db)
    for name, x, y, z in extract_reference_coords(read_gka(S01_GKA)):
        ref_repo.create(
            {"target_name": name, "x": x, "y": y, "z": z, "project_id": project.id}
        )

    import_repo = ImportSessionRepository(db)
    station_repo = StationSetupRepository(db)
    obs_repo = RawObservationRepository(db)
    bessel_repo = BesselObservationRepository(db)
    approx_repo = ApproximateCoordinateRepository(db)
    adjusted_repo = AdjustedCoordinateRepository(db)

    bessel_service = BesselObservationService(
        bessel_repo, station_repo, obs_repo, approx_repo, adjusted_repo
    )
    orchestrator = ImportOrchestratorService(
        import_repo, station_repo, obs_repo, bessel_service
    )
    result = orchestrator.process_gka_import(
        project.id, S01_GKA, read_gka(S01_GKA)
    )
    station_id = result.station_setups[0].id

    approx_service = ApproximateCoordinateService(
        repository=approx_repo,
        repository_bessel_observation=bessel_repo,
        repository_station_setup=station_repo,
        repository_project=project_repo,
        repository_reference_coordinate=ref_repo,
        repository_raw_observation=obs_repo,
        repository_import_session=import_repo,
        repository_adjusted_coordinate=adjusted_repo,
    )
    approx_service.calculate_for_station_setup(station_id)

    return project, station_id


def _build_cascade_services(db) -> tuple[StationSetupService, ProjectService]:
    """Grafo de servicios completo para borrar estacionamientos y proyectos."""
    station_service = StationSetupService(
        repository=StationSetupRepository(db),
        repository_import_session=ImportSessionRepository(db),
        repository_raw_observation=RawObservationRepository(db),
        repository_bessel_observation=BesselObservationRepository(db),
        repository_approximate_coordinate=ApproximateCoordinateRepository(db),
        repository_adjusted_coordinate=AdjustedCoordinateRepository(db),
    )
    import_service = ImportSessionService(
        repository=ImportSessionRepository(db),
        repository_project=ProjectRepository(db),
        repository_station_setup=StationSetupRepository(db),
        station_setup_service=station_service,
    )
    reference_service = ReferenceCoordinateService(
        repository=ReferenceCoordinateRepository(db),
        repository_project=ProjectRepository(db),
    )
    project_service = ProjectService(
        repository=ProjectRepository(db),
        repository_import_session=ImportSessionRepository(db),
        import_session_service=import_service,
        reference_coordinate_service=reference_service,
    )
    return station_service, project_service


def test_delete_project_cascades_everything(db_session):
    project, _station_id = _setup_project_with_adjusted(db_session)

    # Precondición: el proyecto tiene datos en las tablas de la regresión
    # (si no hay ajustadas, este test no probaría nada).
    assert _count(db_session, AdjustedCoordinate) > 0
    assert _count(db_session, ApproximateCoordinate) > 0
    assert _count(db_session, BesselObservation) > 0
    assert _count(db_session, RawObservation) > 0
    refs = _count(db_session, ReferenceCoordinate)
    assert refs > 0
    assert _count(db_session, Coordinate) > refs

    _station_service, project_service = _build_cascade_services(db_session)
    project_service.delete_project(project.id)

    for model in ALL_TABLES:
        assert _count(db_session, model) == 0, model.__tablename__


def test_delete_station_setup_cascades_children(db_session):
    project, station_id = _setup_project_with_adjusted(db_session)
    station_service, _project_service = _build_cascade_services(db_session)

    raw_before = _count(db_session, RawObservation)
    bessel_before = _count(db_session, BesselObservation)

    station_service.delete_station_setup(station_id)

    # Del estacionamiento borrado no queda nada, incluidas las ajustadas y
    # sus filas padre en ``coordinates`` (quedan solo las referencias).
    assert _count(db_session, AdjustedCoordinate) == 0
    assert _count(db_session, ApproximateCoordinate) == 0
    assert _count(db_session, Coordinate) == _count(db_session, ReferenceCoordinate)
    assert _count(db_session, StationSetup) == 3
    assert _count(db_session, RawObservation) < raw_before
    assert _count(db_session, BesselObservation) < bessel_before

    # El proyecto y sus otras sesiones/estacionamientos siguen intactos.
    assert _count(db_session, Project) == 1
    assert project.id is not None
