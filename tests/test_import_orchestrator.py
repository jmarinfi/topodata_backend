"""Camino crítico del orquestador: importación OK + deduplicación por proyecto (A2).

Test a nivel de servicio: prueba directamente la lógica de deduplicación sin el
ruido de auth/upload/CRS. La DB efímera la aporta la fixture ``db_session``.
"""

from pathlib import Path

import pytest

from data.repositories import (
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    ProjectRepository,
    RawObservationRepository,
    StationSetupRepository,
)
from services.bessel_observation_service import BesselObservationService
from services.import_orchestrator_service import ImportOrchestratorService

GKA = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "20250829_013022_20250829_013939.gka"
).read_text(encoding="utf-8")


def _make_project(repo: ProjectRepository, name: str):
    return repo.create(
        {
            "name": name,
            "coordinate_system": "EPSG:25830",
            "a_elip": 6378137.0,
            "b_elip": 6356752.3,
            "f_elip": 0.0033528,
            "inv_f_elip": 298.257223563,
        }
    )


def _orchestrator(db) -> ImportOrchestratorService:
    import_repo = ImportSessionRepository(db)
    station_repo = StationSetupRepository(db)
    obs_repo = RawObservationRepository(db)
    bessel_repo = BesselObservationRepository(db)
    approx_repo = ApproximateCoordinateRepository(db)
    bessel_service = BesselObservationService(
        bessel_repo, station_repo, obs_repo, approx_repo
    )
    return ImportOrchestratorService(
        import_repo, station_repo, obs_repo, bessel_service
    )


def test_import_ok_then_dedup_by_project(db_session):
    project_repo = ProjectRepository(db_session)
    project = _make_project(project_repo, "P1")

    orchestrator = _orchestrator(db_session)

    # Importación OK: 1 estacionamiento (el fichero tiene un único bloque GNV11).
    result = orchestrator.process_gka_import(project.id, "file.gka", GKA)
    assert result.import_session.project_id == project.id
    assert len(result.station_setups) == 1
    assert len(result.raw_observations) > 0

    # Reimportar el mismo fichero en el MISMO proyecto → bloqueado (dedup por proyecto).
    with pytest.raises(ValueError):
        orchestrator.process_gka_import(project.id, "file.gka", GKA)

    # El mismo fichero en un proyecto DISTINTO → permitido (A2: proyectos ≠ obras).
    other_project = _make_project(project_repo, "P2")
    result2 = orchestrator.process_gka_import(other_project.id, "file.gka", GKA)
    assert result2.import_session.project_id == other_project.id
    assert len(result2.station_setups) == 1
