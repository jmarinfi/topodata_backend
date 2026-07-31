"""Test E2E 1 — Levantamiento C56 comparado con los valores del Excel.

Flujo real por HTTP (endpoint de importación hasta hoy sin cubrir):

    register/login → POST /projects → POST /reference-coordinates (×15)
    → POST /projects/import_gka/{id} (fichero 20260121_150005_*.gka)
    → POST /station-setups/{id}/approximate-coordinates
    → GET de resultados

Los 15 puntos con coordenada conocida del C56 y los valores esperados
(etr, k_utm, etr_z, desorientación, coords aproximadas) se transcriben de los
Excel ``Cálculo parámetros v2``, ``Cálculo Desorientación``, ``Cálculo Zest`` y
``Cálculo coord aproximadas`` (los mismos que ya usan ``test_station_position``
y ``test_approximate_coordinate``).

El fichero ``20260121_150005_*`` es una sola jornada (1 estacionamiento, 18
puntos en cara directa + inversa); sus promedios Bessel reproducen los inputs
del Excel (p.ej. C55-R-01E-C → hz 116.2512, v 103.5723).
"""

import pytest

from tests.e2e_helpers import (
    add_references,
    calculate_station,
    create_project,
    get_adjusted,
    get_approx,
    get_bessel,
    get_raw_observations,
    get_station,
    import_gka,
    read_gka,
    recompute_bessel,
    recompute_radiation,
)

# Fichero GKA del levantamiento C56 (1 estacionamiento, 36 obs).
C56_GKA = "20260121_150005_20260121_150438.gka"

# 15 puntos con coordenada conocida observados desde C56 (Excel de Z/desorientación).
# (target_name, x=E, y=N, z). Transcrito de tests/test_station_position.py::_Z_POINTS.
C56_REFERENCES = [
    ("C55-R-01E-C", 428175.22878, 4584168.00555, 43.50666),
    ("C55-R-02E-C", 428167.65241, 4584173.65057, 43.79948),
    ("C56-058-014-20", 428174.88328, 4584119.50644, 28.48947),
    ("C56-058-024-10", 428127.43256, 4584123.2891, 33.4287),
    ("C56-058-024-20", 428127.43707, 4584123.26017, 36.62968),
    ("C56-058-024-22", 428127.90757, 4584114.38102, 36.61848),
    ("C56-058-027-20", 428150.33459, 4584125.80443, 34.62157),
    ("C56-059-003-20", 428219.99187, 4584146.95753, 42.76318),
    ("C56-059-003-22", 428240.08773, 4584136.76845, 40.85964),
    ("C56-059-003-24", 428253.93045, 4584130.40832, 40.88528),
    ("C56-059-009-20", 428272.84479, 4584095.10619, 49.7703),
    ("C56-059-009-22", 428276.60669, 4584088.04858, 51.76567),
    ("C56-059-009-24", 428259.85782, 4584077.92892, 49.77234),
    ("C56-R-01S", 428268.95672, 4584021.11743, 42.2427),
    ("C56-R-02S", 428266.30794, 4584026.24574, 42.25225),
]

# Puntos observados que NO están en las referencias → se ajustan por MMC.
C56_CONTROLS = {"C54-058-007-30-C", "C57-R-03S-C", "C57-R-04S-C"}

# --- Valores esperados del Excel (Cálculo parámetros v2 + coord aprox) ------- #
EXPECTED_ETR_X = 428254.86438
EXPECTED_ETR_Y = 4584084.29001
EXPECTED_K_UTM = 0.99966334542276292
EXPECTED_ETR_Z = 49.898617372443816
EXPECTED_DESORIENTACION = 235.33841324540853
# Coordenada aproximada (radiada) de C55-R-01E-C (Excel "Cálculo coord aprox").
EXPECTED_C55R01_APPROX = (428175.18828641786, 4584168.0478291241, 43.406845391716821)


def _setup_c56(auth_client) -> dict:
    """Crea proyecto + 15 referencias, importa el GKA C56 y lanza el cálculo."""
    project_id, _ = create_project(auth_client, name="E2E C56 vs Excel")
    add_references(auth_client, project_id, C56_REFERENCES)

    result = import_gka(
        auth_client, project_id, C56_GKA, read_gka(C56_GKA)
    )
    assert result["warnings"] == [], result["warnings"]
    station_setups = result["station_setups"]
    assert len(station_setups) == 1, station_setups
    station_id = station_setups[0]["id"]

    calculate_station(auth_client, station_id)

    return {
        "project_id": project_id,
        "station_id": station_id,
        "import_result": result,
    }


class TestE2EC56Excel:
    """Importa el GKA C56 por HTTP y verifica los resultados frente al Excel."""

    def test_import_creates_station_and_observations(self, auth_client):
        setup = _setup_c56(auth_client)
        station_id = setup["station_id"]
        result = setup["import_result"]

        # 1 estacionamiento, 36 obs brutas (18 puntos × 2 caras), 18 Bessel.
        assert len(result["raw_observations"]) == 36
        assert len(result["station_setups"]) == 1

        bessel = get_bessel(auth_client, station_id)
        assert len(bessel) == 18

        raw = get_raw_observations(auth_client, station_id)
        assert len(raw) == 36

    def test_bessel_matches_independent_recompute(self, auth_client):
        """Checkpoint: el Bessel del backend coincide con un recálculo independiente."""
        setup = _setup_c56(auth_client)
        station_id = setup["station_id"]

        raw = get_raw_observations(auth_client, station_id)
        bessel = get_bessel(auth_client, station_id)

        expected = recompute_bessel(raw)
        by_name = {b["target_name"]: b for b in bessel}

        assert set(expected) == set(by_name)
        for name, exp in expected.items():
            got = by_name[name]
            assert got["hz_angle_bessel"] == pytest.approx(exp["hz_b"], abs=1e-4), name
            assert got["v_angle_bessel"] == pytest.approx(exp["v_b"], abs=1e-4), name
            assert got["distance_bessel"] == pytest.approx(exp["d_b"], abs=1e-4), name

    def test_station_scalars_match_excel(self, auth_client):
        """etr_x/y, k_utm, etr_z y desorientación frente a los valores del Excel."""
        setup = _setup_c56(auth_client)
        station = get_station(auth_client, setup["station_id"])

        assert station["etr_x"] == pytest.approx(EXPECTED_ETR_X, abs=0.02)
        assert station["etr_y"] == pytest.approx(EXPECTED_ETR_Y, abs=0.02)
        assert station["k_utm"] == pytest.approx(EXPECTED_K_UTM, abs=1e-5)
        assert station["etr_z"] == pytest.approx(EXPECTED_ETR_Z, abs=5e-3)
        assert station["desorientacion"] == pytest.approx(
            EXPECTED_DESORIENTACION, abs=5e-3
        )

    def test_approximate_coordinates_match_excel(self, auth_client):
        """Coords aproximadas: ancla absoluta del Excel + recálculo de la radiación."""
        setup = _setup_c56(auth_client)
        station_id = setup["station_id"]
        station = get_station(auth_client, station_id)
        approx = {a["target_name"]: a for a in get_approx(auth_client, station_id)}
        bessel = get_bessel(auth_client, station_id)

        # 18 puntos radiados (15 referencias + 3 controles).
        assert len(approx) == 18

        # Ancla absoluta frente al Excel. La tolerancia refleja la incertidumbre
        # de la resección (~2 cm) que se propaga al punto radiado.
        c55 = approx["C55-R-01E-C"]
        assert c55["x"] == pytest.approx(EXPECTED_C55R01_APPROX[0], abs=0.02)
        assert c55["y"] == pytest.approx(EXPECTED_C55R01_APPROX[1], abs=0.02)
        assert c55["z"] == pytest.approx(EXPECTED_C55R01_APPROX[2], abs=0.02)

        # Recálculo independiente de la radiación usando los escalares del propio
        # estacionamiento (etr, k_utm, desorientación) y las observaciones Bessel.
        expected = recompute_radiation(
            bessel,
            etr_x=station["etr_x"],
            etr_y=station["etr_y"],
            etr_z=station["etr_z"],
            k_utm=station["k_utm"],
            desorientacion=station["desorientacion"],
        )
        for name, (ex, ey, ez) in expected.items():
            got = approx[name]
            assert got["x"] == pytest.approx(ex, abs=1e-3), name
            assert got["y"] == pytest.approx(ey, abs=1e-3), name
            assert got["z"] == pytest.approx(ez, abs=1e-3), name

    def test_mmc_produces_adjusted_controls(self, auth_client):
        """El MMC ajusta los 3 puntos de control (redundancia 0 → ajustada ≈ aprox)."""
        setup = _setup_c56(auth_client)
        station_id = setup["station_id"]
        approx = {a["target_name"]: a for a in get_approx(auth_client, station_id)}
        adjusted = get_adjusted(auth_client, station_id)

        adjusted_names = {a["target_name"] for a in adjusted}
        assert adjusted_names == C56_CONTROLS, adjusted_names

        by_name = {a["target_name"]: a for a in adjusted}
        for name in C56_CONTROLS:
            ap = approx[name]
            adj = by_name[name]
            # Sistema determinado: la corrección del MMC es ~0 (coords aprox ya
            # provienen de la radiación de las mismas observaciones).
            assert adj["x"] == pytest.approx(ap["x"], abs=1e-3), name
            assert adj["y"] == pytest.approx(ap["y"], abs=1e-3), name
            # Redundancia 0 → precisiones a posteriori indefinidas (0).
            assert adj["prec_x"] == pytest.approx(0.0, abs=1e-12), name
            assert adj["prec_y"] == pytest.approx(0.0, abs=1e-12), name
