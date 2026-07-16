"""Cálculos de posicionamiento de la estación (B2.2 resección, B2.3 k_utm, B2.4 Z).

Tests del ``StationPositionCalculator``:

Resección (Cassini):
- caso sintético: recupera la estación conocida con tolerancia ajustada;
- oracle real: con los 15 puntos del Excel ``Cálculo desorientación`` se
  recupera la estación (428254.86438, 4584084.29001) dentro de ~2 cm;
- errores: menos de 3 referencias, o menos de 3 observadas.

Factor de escala UTM (k_utm):
- oracle: (428254.86438, 4584084.29001), zona 30T, elipsoide GRS80 → 0.999663;
- errores de zona UTM (número / letra no válidos).

Cota de la estación (ZEST):
- oracle: con los 15 puntos del Excel ``Cálculo de Z del estacionamiento`` →
  ZEST=49.898617 y Z' promedio=49.898549;
- error: sin referencias usables (sin ángulo vertical / altura de señal).
"""

import math

import pytest

from api.schemas import (
    BesselObservationResponse,
    RawObservationResponse,
    ReferenceCoordinateResponse,
)
from services.calculations.station_position_calculator import StationPositionCalculator

GON_R = math.pi / 200.0

# Elipsoide GRS80 (el que usan los Excel / docs/ajustes_topografia.py).
GRS80_A = 6378137.0
GRS80_INV_F = 298.257222101
GRS80_F = 1 / GRS80_INV_F
GRS80_B = GRS80_A * (1 - GRS80_F)


def _ref(name: str, x: float, y: float, z: float = 0.0, project_id: int = 1, id: int = 1):
    return ReferenceCoordinateResponse(
        id=id, target_name=name, x=x, y=y, z=z, project_id=project_id
    )


def _bessel(
    name: str,
    hz_bessel: float = 0.0,
    v_bessel: float = 0.0,
    station_setup_id: int = 1,
    id: int = 1,
):
    return BesselObservationResponse(
        id=id,
        station_setup_id=station_setup_id,
        target_name=name,
        hz_angle_direct=0.0,
        v_angle_direct=0.0,
        distance_direct=0.0,
        hz_angle_inverse=0.0,
        v_angle_inverse=0.0,
        distance_inverse=0.0,
        hz_angle_bessel=hz_bessel,
        v_angle_bessel=v_bessel,
        distance_bessel=0.0,
        hz_angle_delta=0.0,
        v_angle_delta=0.0,
        distance_delta=0.0,
    )


def _raw(name: str, target_height: float = 0.0, station_setup_id: int = 1, id: int = 1):
    return RawObservationResponse(
        id=id,
        station_setup_id=station_setup_id,
        target_name=name,
        target_number=1,
        circle=1,
        hz_angle=0.0,
        v_angle=0.0,
        distance_geom=0.0,
        target_height=target_height,
    )


# ---------------------------------------------------------------------- #
# Inversa planimétrica de Cassini
# ---------------------------------------------------------------------- #


def test_resection_synthetic_recovers_known_station():
    sx, sy = 1000.0, 2000.0
    points = [
        ("A", 1100.0, 2150.0),
        ("B", 880.0, 2080.0),
        ("C", 1060.0, 1880.0),
        ("D", 920.0, 2230.0),
    ]

    refs = [_ref(n, x, y, id=i) for i, (n, x, y) in enumerate(points, 1)]
    bessels = [
        _bessel(n, math.atan2(x - sx, y - sy) / GON_R % 400.0, id=i)
        for i, (n, x, y) in enumerate(points, 1)
    ]

    result = StationPositionCalculator(refs, bessels, GON_R).calculate_resection()

    assert result.etr_x == pytest.approx(sx, abs=1e-6)
    assert result.etr_y == pytest.approx(sy, abs=1e-6)
    assert result.combinations == 4  # C(4, 3)


_EXCEL_POINTS = [
    ("C55-R-01E-C", 428175.22878, 4584168.00555, 116.2512),
    ("C55-R-02E-C", 428167.65241, 4584173.65057, 115.4362),
    ("C56-058-014-20", 428174.88328, 4584119.50644, 91.0666),
    ("C56-058-024-10", 428127.43256, 4584123.2891, 83.5685),
    ("C56-058-024-20", 428127.43707, 4584123.26017, 83.5559),
    ("C56-058-024-22", 428127.90757, 4584114.38102, 79.4773),
    ("C56-058-027-20", 428150.33459, 4584125.80443, 88.7291),
    ("C56-059-003-20", 428219.99187, 4584146.95753, 132.3343),
    ("C56-059-003-22", 428240.08773, 4584136.76845, 147.1884),
    ("C56-059-003-24", 428253.93045, 4584130.40832, 163.3726),
    ("C56-059-009-20", 428272.84479, 4584095.10619, 230.1846),
    ("C56-059-009-22", 428276.60669, 4584088.04858, 253.7641),
    ("C56-059-009-24", 428259.85782, 4584077.92892, 322.2926),
    ("C56-R-01S", 428268.95672, 4584021.11743, 350.6889),
    ("C56-R-02S", 428266.30794, 4584026.24574, 352.2693),
]


def test_resection_excel_oracle_recovers_station():
    refs = [_ref(n, x, y, id=i) for i, (n, x, y, _hz) in enumerate(_EXCEL_POINTS, 1)]
    bessels = [
        _bessel(n, hz, id=i) for i, (n, _x, _y, hz) in enumerate(_EXCEL_POINTS, 1)
    ]

    result = StationPositionCalculator(refs, bessels, GON_R).calculate_resection()

    assert result.etr_x == pytest.approx(428254.86438, abs=0.02)
    assert result.etr_y == pytest.approx(4584084.29001, abs=0.02)
    assert result.combinations > 0


def test_resection_too_few_references_raises():
    refs = [_ref("A", 0.0, 0.0, id=1), _ref("B", 1.0, 1.0, id=2)]
    bessels = [_bessel("A", 10.0, id=1), _bessel("B", 20.0, id=2)]

    with pytest.raises(ValueError):
        StationPositionCalculator(refs, bessels, GON_R)


def test_resection_unobserved_references_raise():
    refs = [
        _ref("A", 0.0, 0.0, id=1),
        _ref("B", 1.0, 1.0, id=2),
        _ref("C", 2.0, 2.0, id=3),
    ]
    bessels = [_bessel("A", 10.0, id=1), _bessel("B", 20.0, id=2)]

    with pytest.raises(ValueError):
        StationPositionCalculator(refs, bessels, GON_R)


# ---------------------------------------------------------------------- #
# Factor de escala UTM (k_utm)
# ---------------------------------------------------------------------- #


def test_kutm_excel_oracle():
    k = StationPositionCalculator.calculate_k_utm(
        etr_x=428254.86438,
        etr_y=4584084.29001,
        zona_utm="30T",
        a_elip=GRS80_A,
        b_elip=GRS80_B,
        f_elip=GRS80_F,
        k_0_adim=0.9996,
    )
    assert k == pytest.approx(0.999663, abs=1e-5)


def test_kutm_bad_zone_number_raises():
    with pytest.raises(ValueError):
        StationPositionCalculator.calculate_k_utm(
            etr_x=428254.86438,
            etr_y=4584084.29001,
            zona_utm="XX T",  # número no entero
            a_elip=GRS80_A,
            b_elip=GRS80_B,
            f_elip=GRS80_F,
            k_0_adim=0.9996,
        )


def test_kutm_bad_zone_letter_raises():
    with pytest.raises(ValueError):
        StationPositionCalculator.calculate_k_utm(
            etr_x=428254.86438,
            etr_y=4584084.29001,
            zona_utm="30Z",  # 'Z' no es banda UTM válida
            a_elip=GRS80_A,
            b_elip=GRS80_B,
            f_elip=GRS80_F,
            k_0_adim=0.9996,
        )


# ---------------------------------------------------------------------- #
# Cota de la estación (etr_z / ZEST)
# ---------------------------------------------------------------------- #

# (nombre, x, y, z, v_bessel) del Excel "Cálculo de Z del estacionamiento".
_Z_POINTS = [
    ("C55-R-01E-C", 428175.22878, 4584168.00555, 43.50666, 103.5723),
    ("C55-R-02E-C", 428167.65241, 4584173.65057, 43.79948, 103.1571),
    ("C56-058-014-20", 428174.88328, 4584119.50644, 28.48947, 115.3586),
    ("C56-058-024-10", 428127.43256, 4584123.2891, 33.4287, 107.8728),
    ("C56-058-024-20", 428127.43707, 4584123.26017, 36.62968, 106.364),
    ("C56-058-024-22", 428127.90757, 4584114.38102, 36.61848, 106.504),
    ("C56-058-027-20", 428150.33459, 4584125.80443, 34.62157, 108.6475),
    ("C56-059-003-20", 428219.99187, 4584146.95753, 42.76318, 106.3989),
    ("C56-059-003-22", 428240.08773, 4584136.76845, 40.85964, 110.5696),
    ("C56-059-003-24", 428253.93045, 4584130.40832, 40.88528, 112.4131),
    ("C56-059-009-20", 428272.84479, 4584095.10619, 49.7703, 100.6912),
    ("C56-059-009-22", 428276.60669, 4584088.04858, 51.76567, 94.913),
    ("C56-059-009-24", 428259.85782, 4584077.92892, 49.77234, 101.777),
    ("C56-R-01S", 428268.95672, 4584021.11743, 42.2427, 107.5897),
    ("C56-R-02S", 428266.30794, 4584026.24574, 42.25225, 108.2854),
]

_ZEST_KW = dict(
    etr_x=428254.86438,
    etr_y=4584084.29001,
    k_utm=0.999663,
    station_height=0.0,
    gon_r=GON_R,
    earth_radius=6378000.0,
    s_sexa_cc=250.0 / 81.0,
    kt_coef_refr=0.13,
    prec_ang_etr=0.5,
)


def test_zest_excel_oracle():
    refs = [
        _ref(n, x, y, z=z, id=i)
        for i, (n, x, y, z, _v) in enumerate(_Z_POINTS, 1)
    ]
    bessels = [
        _bessel(n, v_bessel=v, id=i)
        for i, (n, _x, _y, _z, v) in enumerate(_Z_POINTS, 1)
    ]
    raws = [_raw(n, target_height=0.0, id=i) for i, (n, *_r) in enumerate(_Z_POINTS, 1)]

    result = StationPositionCalculator.calculate_z_est(
        references=refs,
        bessel_observations=bessels,
        raw_observations=raws,
        **_ZEST_KW,
    )

    assert result.z_est == pytest.approx(49.898617, abs=1e-4)
    assert result.z_prima_mean == pytest.approx(49.898549, abs=1e-4)
    assert result.combinations == 15


def test_zest_no_usable_references_raises():
    # Referencia sin observación Bessel (sin ángulo vertical) → nada usable.
    refs = [_ref("A", 0.0, 0.0, z=10.0, id=1)]

    with pytest.raises(ValueError):
        StationPositionCalculator.calculate_z_est(
            references=refs,
            bessel_observations=[],
            raw_observations=[],
            **_ZEST_KW,
        )
