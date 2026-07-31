"""Pipeline completo de coordenadas aproximadas (B2.7–B2.10).

Test de integración a nivel de servicio: siembra un proyecto GRS80 con
referencias y observaciones Bessel del Excel, ejecuta el pipeline entero
y comprueba los oracles (etr_x/y, k_utm, etr_z, desorientación y las
coordenadas aproximadas de C55-R-01E-C).
"""

import math

import pytest

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
from services.approximate_coordinate_service import ApproximateCoordinateService
from services.calculations.matrix_io import from_bytes

# ---------------------------------------------------------------------- #
# Constantes GRS80 (elipsoide del Excel)
# ---------------------------------------------------------------------- #
GRS80_A = 6378137.0
GRS80_B = 6356752.314
GRS80_F = 1.0 / 298.257222101
GRS80_INV_F = 298.257222101

_ZONA_UTM = "30T"

# ---------------------------------------------------------------------- #
# Oracles del Excel (con 15 puntos de referencia)
# ---------------------------------------------------------------------- #
_ETR_X_15 = 428254.86438
_ETR_Y_15 = 4584084.29001
_K_UTM = 0.999663
_ETR_Z_15 = 49.898617
_DESORIENTACION_15 = 235.338413

# ---------------------------------------------------------------------- #
# Oracles recalculados con solo 4 referencias
# (las 4 marcas de referencia reales: C55-R-01E-C, C55-R-02E-C, C56-R-01S, C56-R-02S).
# La estación y la cota difieren ligeramente respecto al Excel porque este
# usaba 15 puntos conocidos en vez de 4.
# ---------------------------------------------------------------------- #
_ETR_X_4 = 428254.861399
_ETR_Y_4 = 4584084.297197
_ETR_Z_4 = 49.963941
_DESORIENTACION_4 = 235.336962
# C55-R-01E-C con 4 refs
_C55_X_4 = 428175.223720
_C55_Y_4 = 4584168.010813
_C55_Z_4 = 43.475480

# ---------------------------------------------------------------------- #
# Puntos de referencia (x, y, z conocidos)
# ---------------------------------------------------------------------- #
_REF_POINTS: list[tuple[str, float, float, float]] = [
    ("C55-R-01E-C", 428175.22878, 4584168.00555, 43.50666),
    ("C55-R-02E-C", 428167.65241, 4584173.65057, 43.79948),
    ("C56-R-01S", 428268.95672, 4584021.11743, 42.2427),
    ("C56-R-02S", 428266.30794, 4584026.24574, 42.25225),
]

# ---------------------------------------------------------------------- #
# Observaciones Bessel de los puntos de referencia
# (hz_bessel, v_bessel, distance_bessel) del Excel.
# ---------------------------------------------------------------------- #
_BESSEL_REF_DATA: list[tuple[str, float, float, float]] = [
    ("C55-R-01E-C", 116.2512, 103.5723, 115.705451),
    ("C55-R-02E-C", 115.4362, 103.1571, 125.225526),
    ("C56-R-01S", 350.6889, 107.5897, 64.695428),
    ("C56-R-02S", 352.2693, 108.2854, 59.190512),
]


# ---------------------------------------------------------------------- #
# Puntos de control (visados que NO son referencia) para tests MMC
# (hz_bessel, v_bessel, distance_bessel) — direcciones distintas de las refs.
# ---------------------------------------------------------------------- #
_CONTROL_DATA: list[tuple[str, float, float, float]] = [
    ("CTRL-01", 200.0, 100.0, 80.0),
    ("CTRL-02", 250.0, 100.0, 100.0),
    ("CTRL-03", 300.0, 100.0, 90.0),
]


def _make_control_data(
    bessel_repo: BesselObservationRepository,
    raw_repo: RawObservationRepository,
    station_setup_id: int,
) -> None:
    """Añade observaciones Bessel (y raw obs mínimas) para puntos de control."""
    for i, (name, hz, v, d) in enumerate(_CONTROL_DATA, start=10):
        bessel_repo.create(
            {
                "station_setup_id": station_setup_id,
                "target_name": name,
                "hz_angle_direct": 0.0,
                "v_angle_direct": 0.0,
                "distance_direct": 0.0,
                "hz_angle_inverse": 0.0,
                "v_angle_inverse": 0.0,
                "distance_inverse": 0.0,
                "hz_angle_bessel": hz,
                "v_angle_bessel": v,
                "distance_bessel": d,
                "hz_angle_delta": 0.0,
                "v_angle_delta": 0.0,
                "distance_delta": 0.0,
            }
        )
        raw_repo.create(
            {
                "station_setup_id": station_setup_id,
                "target_name": name,
                "target_number": i,
                "circle": 1,
                "hz_angle": 0.0,
                "v_angle": 0.0,
                "distance_geom": 0.0,
                "target_height": 0.0,
            }
        )


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #


def _make_project(repo: ProjectRepository) -> int:
    p = repo.create(
        {
            "name": "Proyecto Test Oracle",
            "coordinate_system": "EPSG:25830",
            "zona_utm": _ZONA_UTM,
            "a_elip": GRS80_A,
            "b_elip": GRS80_B,
            "f_elip": GRS80_F,
            "inv_f_elip": GRS80_INV_F,
        }
    )
    return p.id


def _make_import_session(repo: ImportSessionRepository, project_id: int) -> int:
    s = repo.create(
        {
            "project_id": project_id,
            "filename": "test_oracle.gka",
            "content_hash": "test_oracle_hash",
            "raw_file_content": "",
            "kt_coef_refr": 0.13,
            "prec_ang_etr": 0.5,
        }
    )
    return s.id


def _make_station_setup(repo: StationSetupRepository, import_session_id: int) -> int:
    s = repo.create(
        {
            "import_session_id": import_session_id,
            "station_name": "EST-ORACLE",
            "station_height": 0.0,
        }
    )
    return s.id


def _make_refs(repo: ReferenceCoordinateRepository, project_id: int) -> None:
    for name, x, y, z in _REF_POINTS:
        repo.create(
            {
                "target_name": name,
                "x": x,
                "y": y,
                "z": z,
                "project_id": project_id,
            }
        )


def _make_raw_obs(repo: RawObservationRepository, station_setup_id: int) -> None:
    for i, (name, _x, _y, _z) in enumerate(_REF_POINTS, 1):
        repo.create(
            {
                "station_setup_id": station_setup_id,
                "target_name": name,
                "target_number": i,
                "circle": 1,
                "hz_angle": 0.0,
                "v_angle": 0.0,
                "distance_geom": 0.0,
                "target_height": 0.0,
            }
        )


def _make_bessel_obs(repo: BesselObservationRepository, station_setup_id: int) -> None:
    for name, hz, v, d in _BESSEL_REF_DATA:
        repo.create(
            {
                "station_setup_id": station_setup_id,
                "target_name": name,
                "hz_angle_direct": 0.0,
                "v_angle_direct": 0.0,
                "distance_direct": 0.0,
                "hz_angle_inverse": 0.0,
                "v_angle_inverse": 0.0,
                "distance_inverse": 0.0,
                "hz_angle_bessel": hz,
                "v_angle_bessel": v,
                "distance_bessel": d,
                "hz_angle_delta": 0.0,
                "v_angle_delta": 0.0,
                "distance_delta": 0.0,
            }
        )


def _make_service(db) -> ApproximateCoordinateService:
    return ApproximateCoordinateService(
        repository=ApproximateCoordinateRepository(db),
        repository_bessel_observation=BesselObservationRepository(db),
        repository_station_setup=StationSetupRepository(db),
        repository_project=ProjectRepository(db),
        repository_reference_coordinate=ReferenceCoordinateRepository(db),
        repository_raw_observation=RawObservationRepository(db),
        repository_import_session=ImportSessionRepository(db),
        repository_adjusted_coordinate=AdjustedCoordinateRepository(db),
    )


# ---------------------------------------------------------------------- #
# Tests
# ---------------------------------------------------------------------- #


class TestApproximatePipeline:
    """Pipeline completo de coordenadas aproximadas."""

    def test_pipeline_oracles(self, db_session):
        """Ejecuta el pipeline y comprueba los oracles (con 4 referencias)."""
        # --- Arrange: sembrar datos del Excel. ---
        project_repo = ProjectRepository(db_session)
        project_id = _make_project(project_repo)

        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)

        # --- Act ---
        result = service.calculate_for_station_setup(station_setup_id)

        # --- Assert: estación (etr_x/y) — 4-ref oracle. ---
        assert result.etr_x == pytest.approx(_ETR_X_4, abs=1e-3)
        assert result.etr_y == pytest.approx(_ETR_Y_4, abs=1e-3)

        # --- Assert: factor de escala UTM (estable, mismo que con 15 refs). ---
        assert result.k_utm == pytest.approx(_K_UTM, abs=1e-5)

        # --- Assert: cota de la estación — 4-ref oracle. ---
        assert result.etr_z == pytest.approx(_ETR_Z_4, abs=1e-3)

        # --- Assert: desorientación — 4-ref oracle. ---
        assert result.desorientacion == pytest.approx(_DESORIENTACION_4, abs=1e-3)

        # --- Assert: coordenadas aproximadas persistidas. ---
        assert len(result.approximate_coordinates) == 4
        names = {c.target_name for c in result.approximate_coordinates}
        assert names == {r[0] for r in _REF_POINTS}

        # --- Assert: C55-R-01E-C — 4-ref oracle. ---
        c55 = next(
            c for c in result.approximate_coordinates if c.target_name == "C55-R-01E-C"
        )
        assert c55.x == pytest.approx(_C55_X_4, abs=1e-3)
        assert c55.y == pytest.approx(_C55_Y_4, abs=1e-3)
        assert c55.z == pytest.approx(_C55_Z_4, abs=1e-3)

    def test_pipeline_persists_etr_fields_on_station_setup(self, db_session):
        """Los campos etr_*, k_utm y desorientacion se persisten en el modelo."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)
        service.calculate_for_station_setup(station_setup_id)

        # Recargar de DB.
        station = StationSetupRepository(db_session).get(station_setup_id)
        assert station.etr_x == pytest.approx(_ETR_X_4, abs=1e-3)
        assert station.etr_y == pytest.approx(_ETR_Y_4, abs=1e-3)
        assert station.etr_z == pytest.approx(_ETR_Z_4, abs=1e-3)
        assert station.k_utm == pytest.approx(_K_UTM, abs=1e-5)
        assert station.desorientacion == pytest.approx(_DESORIENTACION_4, abs=1e-3)

    def test_pipeline_idempotent(self, db_session):
        """Dos llamadas consecutivas producen el mismo resultado (idempotencia)."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)

        result1 = service.calculate_for_station_setup(station_setup_id)
        count1 = len(result1.approximate_coordinates)

        result2 = service.calculate_for_station_setup(station_setup_id)
        count2 = len(result2.approximate_coordinates)

        # Mismo número de coordenadas (no se duplican).
        assert count1 == count2 == 4

        # Mismos valores de estación.
        assert result2.etr_x == pytest.approx(result1.etr_x)
        assert result2.etr_y == pytest.approx(result1.etr_y)
        assert result2.k_utm == pytest.approx(result1.k_utm)

    def test_pipeline_no_station_setup_raises(self, db_session):
        """Estacionamiento inexistente → ValueError."""
        service = _make_service(db_session)
        with pytest.raises(ValueError, match="no encontrado"):
            service.calculate_for_station_setup(9999)

    def test_pipeline_no_bessel_raises(self, db_session):
        """Sin observaciones Bessel → ValueError."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)

        service = _make_service(db_session)
        with pytest.raises(ValueError, match="Bessel"):
            service.calculate_for_station_setup(station_setup_id)

    def test_pipeline_insufficient_refs_raises(self, db_session):
        """Menos de 3 referencias → ValueError."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        # Solo 2 referencias (necesita ≥3 para Cassini).
        ref_repo = ReferenceCoordinateRepository(db_session)
        for i, (name, x, y, z) in enumerate(_REF_POINTS[:2]):
            ref_repo.create(
                {
                    "target_name": name,
                    "x": x,
                    "y": y,
                    "z": z,
                    "project_id": project_id,
                }
            )

        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)
        with pytest.raises(ValueError, match="3"):
            service.calculate_for_station_setup(station_setup_id)

    def test_pipeline_no_zona_utm_raises(self, db_session):
        """Proyecto sin zona_utm → ValueError."""
        project_repo = ProjectRepository(db_session)
        p = project_repo.create(
            {
                "name": "Sin Zona",
                "coordinate_system": "EPSG:25830",
                "a_elip": GRS80_A,
                "b_elip": GRS80_B,
                "f_elip": GRS80_F,
                "inv_f_elip": GRS80_INV_F,
            }
        )
        # No se asigna zona_utm (queda None).

        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), p.id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), p.id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)
        with pytest.raises(ValueError, match="zona UTM"):
            service.calculate_for_station_setup(station_setup_id)


class TestMMCIntegration:
    """Pruebas de integración del MMC en el pipeline."""

    def test_no_control_points_skips_mmc(self, db_session):
        """Sin puntos de control → MMC omitido con warning, sin registros ajustados."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)

        service = _make_service(db_session)
        result = service.calculate_for_station_setup(station_setup_id)

        # Warning de MMC omitido.
        assert any("MMC omitido" in w for w in result.warnings)
        assert result.adjusted_coordinates == []
        assert result.desv_post is None
        assert result.num_equations is None
        assert result.num_unknowns is None

        # Sin registros ajustados en DB.
        adjusted = AdjustedCoordinateRepository(db_session).get_all()
        assert len(adjusted) == 0

        # Matrices sin poblar (sin puntos de control).
        station = StationSetupRepository(db_session).get(station_setup_id)
        assert station.a_matrix is None

    def test_matrices_populated_with_control_points(self, db_session):
        """Con puntos de control → las 18 columnas *_matrix de StationSetup se pueblan."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)
        _make_control_data(
            BesselObservationRepository(db_session),
            RawObservationRepository(db_session),
            station_setup_id,
        )

        service = _make_service(db_session)
        service.calculate_for_station_setup(station_setup_id)

        station = StationSetupRepository(db_session).get(station_setup_id)

        matrix_cols = [
            "a_matrix", "p_matrix", "l_matrix", "x_matrix",
            "v_matrix", "n_matrix", "inver_n_matrix",
            "tra_a_matrix", "tra_a_p_matrix", "t_matrix",
            "tra_v_p_matrix", "prec_matrix", "adjust_coord_matrix",
        ]
        for col in matrix_cols:
            val = getattr(station, col)
            assert val is not None, f"{col} debería estar poblada"
            arr = from_bytes(val)
            assert arr.size > 0, f"{col} no debería estar vacía"

        a = from_bytes(station.a_matrix)
        n_ctrl = len(_CONTROL_DATA)
        assert a.shape == (2 * n_ctrl, 2 * n_ctrl)

        for col in (
            "desv_post_matrix", "var_post_matrix",
            "num_equations_matrix", "num_unknowns_matrix",
            "inter_conf_matrix",
        ):
            assert getattr(station, col) is not None, f"{col} debería estar poblada"

    def test_adjusted_coordinates_created(self, db_session):
        """Con puntos de control → registros AdjustedCoordinate con x, y, prec_x, prec_y."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)
        _make_control_data(
            BesselObservationRepository(db_session),
            RawObservationRepository(db_session),
            station_setup_id,
        )

        service = _make_service(db_session)
        result = service.calculate_for_station_setup(station_setup_id)

        control_names = {d[0] for d in _CONTROL_DATA}
        assert len(result.adjusted_coordinates) == len(control_names)

        for adj in result.adjusted_coordinates:
            assert adj.target_name in control_names
            assert adj.prec_x >= 0
            assert adj.prec_y >= 0
            assert adj.type == "adjusted"

        db_adjusted = AdjustedCoordinateRepository(db_session).get_by_station_setup(
            station_setup_id
        )
        assert len(db_adjusted) == len(control_names)

    def test_pipeline_idempotent_with_control_points(self, db_session):
        """Con puntos de control: dos runs no duplican matrices ni ajustadas."""
        project_id = _make_project(ProjectRepository(db_session))
        import_session_id = _make_import_session(
            ImportSessionRepository(db_session), project_id
        )
        station_setup_id = _make_station_setup(
            StationSetupRepository(db_session), import_session_id
        )

        _make_refs(ReferenceCoordinateRepository(db_session), project_id)
        _make_raw_obs(RawObservationRepository(db_session), station_setup_id)
        _make_bessel_obs(BesselObservationRepository(db_session), station_setup_id)
        _make_control_data(
            BesselObservationRepository(db_session),
            RawObservationRepository(db_session),
            station_setup_id,
        )

        service = _make_service(db_session)

        result1 = service.calculate_for_station_setup(station_setup_id)
        count_adj1 = len(result1.adjusted_coordinates)
        count_approx1 = len(result1.approximate_coordinates)

        result2 = service.calculate_for_station_setup(station_setup_id)
        count_adj2 = len(result2.adjusted_coordinates)
        count_approx2 = len(result2.approximate_coordinates)

        assert count_adj1 == count_adj2
        assert count_approx1 == count_approx2

        # Total: 4 refs + N controles (approx) / N controles (adjusted).
        assert count_approx1 == 4 + len(_CONTROL_DATA)
        assert count_adj1 == len(_CONTROL_DATA)
