"""Test E2E 2 — Levantamiento S01 verificado por recálculo (oráculo del Colab).

A diferencia del C56 (que tiene Excel numérico), el S01
(``20251112_200023_20251112_210627.gka``) no dispone de oráculo numérico: se
verifica recomputando cada etapa con una implementación independiente de la
lógica del Colab (``ajustes_topografia.py``).

El fichero S01 es autodescriptivo para referencias: las columnas 19/20/21
llevan el X/Y/Z de cada referencia (p. ej. ``S01-R01``). Son 15 referencias
(nombres con ``-R``) + ~48 puntos de control, en 4 ocupaciones de la estación
``S01``.

Flujo HTTP real:

    register/login → POST /projects → POST /reference-coordinates (refs del GKA)
    → POST /projects/import_gka/{id} (4 estacionamientos)
    → POST /station-setups/{id}/approximate-coordinates (×4)
    → GET de resultados y recálculo etapa a etapa.
"""

import pytest

from tests.e2e_helpers import (
    add_references,
    calculate_station,
    create_project,
    extract_reference_coords,
    get_adjusted,
    get_approx,
    get_bessel,
    get_raw_observations,
    get_station,
    import_gka,
    oracle_desorientacion,
    oracle_k_utm,
    oracle_resection,
    oracle_z_est,
    read_gka,
    recompute_bessel,
    recompute_radiation,
)

S01_GKA = "20251112_200023_20251112_210627.gka"

ZONA_UTM = "30T"

# Imports para la verificación de matrices MMC a nivel de servicio (Class B).
import numpy as np  # noqa: E402

from data.repositories import (  # noqa: E402
    AdjustedCoordinateRepository,
    ApproximateCoordinateRepository,
    BesselObservationRepository,
    ImportSessionRepository,
    ProjectRepository,
    RawObservationRepository,
    ReferenceCoordinateRepository,
    StationSetupRepository,
)
from services.approximate_coordinate_service import (  # noqa: E402
    ApproximateCoordinateService,
)
from services.bessel_observation_service import BesselObservationService  # noqa: E402
from services.calculations.matrix_io import from_bytes, scalar_from_bytes  # noqa: E402
from services.import_orchestrator_service import ImportOrchestratorService  # noqa: E402


def _is_reference_name(name: str) -> bool:
    """Patrón del usuario: '<estación>-R…' (letra R tras el nombre)."""
    parts = name.split("-", 1)
    return len(parts) == 2 and parts[1].startswith("R")


def _setup_s01(auth_client) -> dict:
    """Crea proyecto, añade las referencias del GKA, importa y calcula (×4)."""
    project_id, project = create_project(auth_client, name="E2E S01 por recálculo")

    refs = extract_reference_coords(read_gka(S01_GKA))
    assert len(refs) == 15, refs
    assert all(_is_reference_name(n) for n, *_ in refs), refs
    add_references(auth_client, project_id, refs)

    result = import_gka(auth_client, project_id, S01_GKA, read_gka(S01_GKA))
    assert result["warnings"] == [], result["warnings"]
    station_ids = [s["id"] for s in result["station_setups"]]
    assert len(station_ids) == 4, station_ids

    for sid in station_ids:
        calculate_station(auth_client, sid)

    return {"project": project, "refs": refs, "station_ids": station_ids}


class TestE2ES01Recompute:
    """Importa el GKA S01 por HTTP y verifica cada etapa por recálculo."""

    def test_references_match_reference_pattern(self, auth_client):
        refs = extract_reference_coords(read_gka(S01_GKA))
        names = [n for n, *_ in refs]
        assert len(names) == 15
        assert all(_is_reference_name(n) for n in names)
        for expected in ("S01-R01", "S01-R04B", "S02-R01", "S02-R02", "S01-R07B"):
            assert expected in names, expected

    def test_import_creates_four_occupations(self, auth_client):
        setup = _setup_s01(auth_client)
        assert len(setup["station_ids"]) == 4

    def test_each_station_pipeline_matches_recompute(self, auth_client):
        setup = _setup_s01(auth_client)
        project = setup["project"]
        refs = setup["refs"]
        ref_names = {n for n, *_ in refs}

        for sid in setup["station_ids"]:
            station = get_station(auth_client, sid)
            raw = get_raw_observations(auth_client, sid)
            bessel = get_bessel(auth_client, sid)
            approx_by = {a["target_name"]: a for a in get_approx(auth_client, sid)}

            b_by = {b["target_name"]: b for b in bessel}
            hz_by = {b["target_name"]: b["hz_angle_bessel"] for b in bessel}
            v_by = {b["target_name"]: b["v_angle_bessel"] for b in bessel}
            # target_height por target (la primera observación; en S01 es 0.0).
            th_by: dict[str, float] = {}
            for o in raw:
                th_by.setdefault(o["target_name"], o.get("target_height") or 0.0)

            # --- Bessel: recálculo independiente desde las obs brutas -------- #
            exp_b = recompute_bessel(raw)
            assert set(exp_b) == set(b_by), sid
            for name, e in exp_b.items():
                g = b_by[name]
                assert g["hz_angle_bessel"] == pytest.approx(e["hz_b"], abs=1e-4), (sid, name)
                assert g["v_angle_bessel"] == pytest.approx(e["v_b"], abs=1e-4), (sid, name)
                assert g["distance_bessel"] == pytest.approx(e["d_b"], abs=1e-4), (sid, name)

            # --- Resección (Cassini) ----------------------------------------- #
            ex, ey = oracle_resection(refs, hz_by)
            assert station["etr_x"] == pytest.approx(ex, abs=1e-6), sid
            assert station["etr_y"] == pytest.approx(ey, abs=1e-6), sid

            # --- k_utm -------------------------------------------------------- #
            k = oracle_k_utm(
                station["etr_x"], station["etr_y"], ZONA_UTM,
                project["a_elip"], project["b_elip"], project["f_elip"],
            )
            assert station["k_utm"] == pytest.approx(k, abs=1e-9), sid

            # --- Cota de la estación (ZEST) ---------------------------------- #
            z = oracle_z_est(
                refs, v_by, th_by,
                station["etr_x"], station["etr_y"], station["k_utm"],
                station.get("station_height"),
            )
            assert station["etr_z"] == pytest.approx(z, abs=1e-6), sid

            # --- Desorientación ---------------------------------------------- #
            des = oracle_desorientacion(refs, hz_by, station["etr_x"], station["etr_y"])
            assert station["desorientacion"] == pytest.approx(des, abs=1e-6), sid

            # --- Radiación (coords aproximadas) ------------------------------ #
            exp_r = recompute_radiation(
                bessel, station["etr_x"], station["etr_y"], station["etr_z"],
                station["k_utm"], station["desorientacion"],
            )
            for name, (x, y, zv) in exp_r.items():
                g = approx_by[name]
                assert g["x"] == pytest.approx(x, abs=1e-3), (sid, name)
                assert g["y"] == pytest.approx(y, abs=1e-3), (sid, name)
                assert g["z"] == pytest.approx(zv, abs=1e-3), (sid, name)

            # --- MMC: controles (puntos no referencia) ajustados ------------ #
            adjusted_by = {a["target_name"]: a for a in get_adjusted(auth_client, sid)}
            control_names = set(b_by) - ref_names
            assert set(adjusted_by) == control_names, (
                sid, sorted(set(adjusted_by) ^ control_names)
            )
            for name in control_names:
                ap = approx_by[name]
                adj = adjusted_by[name]
                # Sistema determinado (redundancia 0): ajustada ≈ aproximada.
                assert adj["x"] == pytest.approx(ap["x"], abs=1e-3), (sid, name)
                assert adj["y"] == pytest.approx(ap["y"], abs=1e-3), (sid, name)
                assert adj["prec_x"] == pytest.approx(0.0, abs=1e-9), (sid, name)
                assert adj["prec_y"] == pytest.approx(0.0, abs=1e-9), (sid, name)


# --------------------------------------------------------------------------- #
# Class B — Álgebra de las matrices MMC persistidas (nivel de servicio)
# --------------------------------------------------------------------------- #
def _setup_s01_first_station(db_session) -> tuple[StationSetupRepository, int]:
    """Crea proyecto + referencias, importa el GKA S01 y calcula el 1er estacionamiento.

    A nivel de servicio (db_session) para tener acceso directo a los blobs de
    matrices persistidos en ``StationSetup``.
    """
    project_repo = ProjectRepository(db_session)
    project = project_repo.create(
        {
            "name": "E2E S01 MMC matrices",
            "coordinate_system": "EPSG:25830",
            "zona_utm": ZONA_UTM,
            "a_elip": 6378137.0,
            "b_elip": 6356752.314,
            "f_elip": 1.0 / 298.257222101,
            "inv_f_elip": 298.257222101,
        }
    )

    ref_repo = ReferenceCoordinateRepository(db_session)
    for name, x, y, z in extract_reference_coords(read_gka(S01_GKA)):
        ref_repo.create(
            {"target_name": name, "x": x, "y": y, "z": z, "project_id": project.id}
        )

    import_repo = ImportSessionRepository(db_session)
    station_repo = StationSetupRepository(db_session)
    obs_repo = RawObservationRepository(db_session)
    bessel_repo = BesselObservationRepository(db_session)
    approx_repo = ApproximateCoordinateRepository(db_session)
    adjusted_repo = AdjustedCoordinateRepository(db_session)

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

    return station_repo, station_id


class TestE2ES01MmcMatrices:
    """Verifica que las matrices MMC persistidas son algebraicamente consistentes.

    El S01 no tiene oráculo Excel para las matrices; en su lugar se comprueba
    la cadena del MMC (A, P, L, N, N⁻¹, x, v) leyendo los blobs de
    ``StationSetup`` y verificando las identidades que deben cumplir.
    """

    def test_mmc_matrices_self_consistent(self, db_session):
        station_repo, station_id = _setup_s01_first_station(db_session)
        station = station_repo.get(station_id)

        a = from_bytes(station.a_matrix)
        p = from_bytes(station.p_matrix)
        ell = from_bytes(station.l_matrix)
        n = from_bytes(station.n_matrix)
        n_inv = from_bytes(station.inver_n_matrix)
        x = from_bytes(station.x_matrix)
        v = from_bytes(station.v_matrix)
        tra_a = from_bytes(station.tra_a_matrix)

        num_eq = scalar_from_bytes(station.num_equations_matrix)
        num_unk = scalar_from_bytes(station.num_unknowns_matrix)

        # Cada control observado una vez → 2 ecuaciones y 2 incógnitas → red. 0.
        assert num_eq == num_unk
        assert a.shape == (num_eq, num_unk)

        # tra_a == Aᵀ
        assert np.allclose(tra_a, a.T, atol=1e-9)

        # N = Aᵀ · P · A
        assert np.allclose(n, a.T @ p @ a, atol=1e-6)

        # N⁻¹ · N = I
        assert np.allclose(n_inv @ n, np.eye(num_unk), atol=1e-6)

        # x̂ = N⁻¹ · Aᵀ · P · L
        x_expected = n_inv @ a.T @ p @ ell
        assert np.allclose(np.ravel(x), np.ravel(x_expected), atol=1e-6)

        # v = A · x̂ − L
        v_expected = a @ x - ell
        assert np.allclose(np.ravel(v), np.ravel(v_expected), atol=1e-6)

        # Sistema compatible determinado → residuos ≈ 0.
        assert np.allclose(np.ravel(v), 0.0, atol=1e-6)
