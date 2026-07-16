"""Desorientación del estacionamiento (B2.5).

Tests del ``ApproximateCoordinateCalculator.calculate_desorientacion``:

- oracle: con los 15 puntos del Excel ``Cálculo desorientación`` y la estación
  (428254.86438, 4584084.29001) → ε media = 235.338413 gon;
- referencia única (C55-R-01E-C) → ε = 235.338523 gon (valor por punto del Excel);
- error: sin referencias observadas.
"""

import math

import pytest

from api.schemas import BesselObservationResponse, ReferenceCoordinateResponse
from services.calculations.approximate_coordinate_calculator import (
    ApproximateCoordinateCalculator,
)

GON_R = math.pi / 200.0

ETR_X = 428254.86438
ETR_Y = 4584084.29001


def _ref(name: str, x: float, y: float, project_id: int = 1, id: int = 1):
    return ReferenceCoordinateResponse(
        id=id, target_name=name, x=x, y=y, z=0.0, project_id=project_id
    )


def _bessel(name: str, hz_bessel: float, station_setup_id: int = 1, id: int = 1):
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
        v_angle_bessel=0.0,
        distance_bessel=0.0,
        hz_angle_delta=0.0,
        v_angle_delta=0.0,
        distance_delta=0.0,
    )


# (nombre, x, y, hz_bessel) del Excel "Cálculo desorientación".
_DESORIENT_POINTS = [
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


def test_desorientacion_excel_oracle():
    refs = [
        _ref(n, x, y, id=i) for i, (n, x, y, _hz) in enumerate(_DESORIENT_POINTS, 1)
    ]
    bessels = [
        _bessel(n, hz, id=i) for i, (n, _x, _y, hz) in enumerate(_DESORIENT_POINTS, 1)
    ]

    result = ApproximateCoordinateCalculator.calculate_desorientacion(
        ETR_X, ETR_Y, refs, bessels, GON_R
    )

    assert result.desorientacion == pytest.approx(235.338413, abs=1e-5)
    assert result.combinations == 15


def test_desorientacion_single_reference_matches_excel_point():
    # Con una sola referencia, la ε es la suya (C55-R-01E-C → 235.338523).
    refs = [_ref("C55-R-01E-C", 428175.22878, 4584168.00555, id=1)]
    bessels = [_bessel("C55-R-01E-C", 116.2512, id=1)]

    result = ApproximateCoordinateCalculator.calculate_desorientacion(
        ETR_X, ETR_Y, refs, bessels, GON_R
    )

    assert result.desorientacion == pytest.approx(235.338523, abs=1e-5)
    assert result.combinations == 1


def test_desorientacion_no_observed_references_raises():
    refs = [_ref("A", 0.0, 0.0, id=1)]

    with pytest.raises(ValueError):
        ApproximateCoordinateCalculator.calculate_desorientacion(
            0.0, 0.0, refs, [], GON_R
        )


# ====================================================================== #
# B2.6 · Radiación (coordenadas aproximadas)
# ====================================================================== #

# Constantes del Colab / Excel.
_R_CC = 2000000.0 / math.pi
_EARTH_RADIUS = 6378000.0
_KT_COEF_REFR = 0.13

# Parámetros de la estación (oracles del Excel).
_ETR_X = 428254.86438
_ETR_Y = 4584084.29001
_ETR_Z = 49.898617
_K_UTM = 0.999663
_DESORIENTACION = 235.338413


def _bessel_full(
    name: str,
    hz_bessel: float,
    v_bessel: float,
    distance_bessel: float,
    station_setup_id: int = 1,
    id: int = 1,
) -> BesselObservationResponse:
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
        distance_bessel=distance_bessel,
        hz_angle_delta=0.0,
        v_angle_delta=0.0,
        distance_delta=0.0,
    )


def test_radiacion_c55_r01ec_oracle():
    """C55-R-01E-C contra los oracles del Excel 'Cálculo coord aproximadas'."""
    from services.calculations.approximate_coordinate_calculator import (
        RadiacionResult,
    )

    # Bessel de C55-R-01E-C: hz=116.2512 gon, v=103.5723 gon, d≈115.7645 m.
    bessel = _bessel_full("C55-R-01E-C", 116.2512, 103.5723, 115.7645)

    result: RadiacionResult = ApproximateCoordinateCalculator.calculate_radiacion(
        bessel=bessel,
        etr_x=_ETR_X,
        etr_y=_ETR_Y,
        etr_z=_ETR_Z,
        k_utm=_K_UTM,
        desorientacion=_DESORIENTACION,
        gon_r=GON_R,
        earth_radius=_EARTH_RADIUS,
        r_cc=_R_CC,
        kt_coef_refr=_KT_COEF_REFR,
    )

    # Oracles del plan B2.6 (redondeados a 6 decimales en el Excel).
    assert result.x == pytest.approx(428175.188286, abs=1e-4)
    assert result.y == pytest.approx(4584168.047829, abs=1e-4)
    assert result.z == pytest.approx(43.406845, abs=1e-4)

    # Intermedios.
    assert result.w_cc == pytest.approx(11.555028, abs=1e-4)
    assert result.r_cc == pytest.approx(1.502154, abs=1e-4)
    assert result.dist_utm == pytest.approx(115.601264, abs=1e-4)
    assert result.acimut == pytest.approx(351.589613, abs=1e-4)


def test_radiacion_target_name_preserved():
    """El nombre del objetivo se conserva en el resultado."""
    bessel = _bessel_full("C56-R-01S", 350.6889, 107.5897, 200.0)

    result = ApproximateCoordinateCalculator.calculate_radiacion(
        bessel=bessel,
        etr_x=_ETR_X,
        etr_y=_ETR_Y,
        etr_z=_ETR_Z,
        k_utm=_K_UTM,
        desorientacion=_DESORIENTACION,
        gon_r=GON_R,
        earth_radius=_EARTH_RADIUS,
        r_cc=_R_CC,
        kt_coef_refr=_KT_COEF_REFR,
    )

    assert result.target_name == "C56-R-01S"


def test_radiacion_all_returns_one_per_bessel():
    """calculate_all_radiaciones devuelve tantos resultados como observaciones."""
    bessels = [_bessel_full("A", 10.0, 100.0, 50.0, id=i) for i in range(1, 6)]

    results = ApproximateCoordinateCalculator.calculate_all_radiaciones(
        bessel_observations=bessels,
        etr_x=_ETR_X,
        etr_y=_ETR_Y,
        etr_z=_ETR_Z,
        k_utm=_K_UTM,
        desorientacion=_DESORIENTACION,
        gon_r=GON_R,
        earth_radius=_EARTH_RADIUS,
        r_cc=_R_CC,
        kt_coef_refr=_KT_COEF_REFR,
    )

    assert len(results) == 5
    assert {r.target_name for r in results} == {"A"}


def test_radiacion_empty_list_returns_empty():
    """Lista vacía → lista vacía."""
    results = ApproximateCoordinateCalculator.calculate_all_radiaciones(
        bessel_observations=[],
        etr_x=_ETR_X,
        etr_y=_ETR_Y,
        etr_z=_ETR_Z,
        k_utm=_K_UTM,
        desorientacion=_DESORIENTACION,
        gon_r=GON_R,
        earth_radius=_EARTH_RADIUS,
        r_cc=_R_CC,
        kt_coef_refr=_KT_COEF_REFR,
    )

    assert results == []
