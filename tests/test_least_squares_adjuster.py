import math

import numpy as np
import pytest

from services.calculations.least_squares_adjuster import (
    INTER_CONF_DEFAULT,
    LeastSquaresAdjuster,
    LeastSquaresResult,
    LsTarget,
)

GON_R = math.pi / 200.0
R_CC = 2000000.0 / math.pi
S_SEXA_CC = 250.0 / 81.0

PREC_ANG_ETR = 0.5
PREC_DIST_MM = 0.8
PREC_DIST_PPM = 1.0

STATION_X = 0.0
STATION_Y = 0.0

# P1: valores del Excel usados como oraculo para A
P1_X = -127.4318
P1_Y = 38.99909
P1_DE = -127.4318
P1_DN = 38.99909
P1_DIST_CALC = math.hypot(P1_DE, P1_DN)  # ~133.26589
P1_DIST_UTM = 133.26547
P1_ACIMUT = 318.92

# P2: segunda referencia con distinta distancia para test de sigma_dist
P2_X = 80.0
P2_Y = 30.0
P2_DIST_UTM = 87.39099
P2_DE = P2_X - STATION_X
P2_DN = P2_Y - STATION_Y
P2_ACIMUT = (math.atan2(P2_DE, P2_DN) / GON_R) % 400.0

# P3, P4: sinteticos para test de redundancia
P3_X = 50.0
P3_Y = -30.0
P3_DIST_UTM = 58.31
P3_DE = P3_X - STATION_X
P3_DN = P3_Y - STATION_Y
P3_ACIMUT = (math.atan2(P3_DE, P3_DN) / GON_R) % 400.0

P4_X = -60.0
P4_Y = -80.0
P4_DIST_UTM = 100.0
P4_DE = P4_X - STATION_X
P4_DN = P4_Y - STATION_Y
P4_ACIMUT = (math.atan2(P4_DE, P4_DN) / GON_R) % 400.0


def _make_adjuster(*targets: LsTarget) -> LeastSquaresAdjuster:
    return LeastSquaresAdjuster(
        station_x=STATION_X,
        station_y=STATION_Y,
        targets=list(targets),
        gon_r=GON_R,
        r_cc=R_CC,
        s_sexa_cc=S_SEXA_CC,
        prec_ang_etr=PREC_ANG_ETR,
        prec_dist_mm=PREC_DIST_MM,
        prec_dist_ppm=PREC_DIST_PPM,
    )


def _p1_target(**overrides) -> LsTarget:
    return LsTarget(
        target_name="P1",
        approx_x=P1_X,
        approx_y=P1_Y,
        dist_utm=P1_DIST_UTM,
        acimut_observado=P1_ACIMUT,
        **overrides,
    )


def _p2_target(**overrides) -> LsTarget:
    return LsTarget(
        target_name="P2",
        approx_x=P2_X,
        approx_y=P2_Y,
        dist_utm=P2_DIST_UTM,
        acimut_observado=P2_ACIMUT,
        **overrides,
    )


# ------------------------------------------------------------------ #
# (a) Oraculos de precision (sigma_dir / sigma_dist)
# ------------------------------------------------------------------ #

def test_sigma_dir_against_excel_oracle():
    """sigma_dir[0] ~ 3.4539248288 (M10 del Excel)."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    expected = 3.4539248288
    assert r.sigma_dir[0] == pytest.approx(expected, rel=1e-6)


def test_sigma_dist_p1_against_excel_oracle():
    """sigma_dist para dist_utm ~133.27 m debe ser ~9.33265e-4 (N11)."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    expected = 9.33265e-4
    assert r.sigma_dist[0] == pytest.approx(expected, rel=1e-4)


def test_sigma_dist_p2_against_excel_oracle():
    """sigma_dist para dist_utm ~87.39 m debe ser ~8.87391e-4 (N10)."""
    t = _p2_target()
    r = _make_adjuster(t).calculate()
    expected = 8.87391e-4
    assert r.sigma_dist[0] == pytest.approx(expected, rel=1e-4)


# ------------------------------------------------------------------ #
# (b) Coeficientes de A
# ------------------------------------------------------------------ #

def test_a_matrix_direction_coefficients():
    """A[dir,dx] ~ 1397.97, A[dir,dy] ~ 4567.94 (celdas C15/D15)."""
    r = _make_adjuster(_p1_target()).calculate()
    assert r.a[0, 0] == pytest.approx(1397.97, rel=1e-4)
    assert r.a[0, 1] == pytest.approx(4567.94, rel=1e-4)


def test_a_matrix_distance_coefficients():
    """Fila distancia: A[dist,dx] = DE/dist_utm, A[dist,dy] = DN/dist_utm."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    assert r.a[1, 0] == pytest.approx(P1_DE / P1_DIST_UTM, rel=1e-8)
    assert r.a[1, 1] == pytest.approx(P1_DN / P1_DIST_UTM, rel=1e-8)


def test_a_matrix_shape():
    """Con 2 observaciones (2 puntos), A debe ser 4x4."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    assert r.a.shape == (4, 4)


# ------------------------------------------------------------------ #
# (c) Pesos de P
# ------------------------------------------------------------------ #

def test_p_matrix_direction_weight():
    """P[dir,dir] = 1/sigma_dir^2 ~ 0.083825."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    expected = 1.0 / (r.sigma_dir[0] ** 2)
    assert r.p[0, 0] == pytest.approx(expected, rel=1e-8)


def test_p_matrix_distance_weight():
    """P[dist,dist] = 1/sigma_dist^2."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    expected = 1.0 / (r.sigma_dist[0] ** 2)
    assert r.p[1, 1] == pytest.approx(expected, rel=1e-8)


def test_p_matrix_diagonal():
    """P debe ser diagonal (elementos fuera de la diagonal nulos)."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    n_eq = 4
    for i in range(n_eq):
        for j in range(n_eq):
            if i != j:
                assert r.p[i, j] == 0.0


# ------------------------------------------------------------------ #
# (d) Identidades algebraicas
# ------------------------------------------------------------------ #

def test_algebraic_n_equals_ata_p_a():
    """N = A^T @ P @ A."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    n_check = r.tra_a @ r.p @ r.a
    assert np.allclose(r.n, n_check, rtol=1e-10)


def test_algebraic_x_equals_inver_n_t():
    """x = inver_n @ t por definicion."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    x_check = r.inver_n @ r.t
    assert np.allclose(r.x, x_check, rtol=1e-10)


def test_algebraic_v_equals_ax_minus_l():
    """v = A @ x - L."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    v_check = r.a @ r.x - r.l
    assert np.allclose(r.v, v_check, rtol=1e-10)


def test_algebraic_vtpv_non_negative():
    """v^T @ P @ v >= 0."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    vtpv = float(r.v @ r.p @ r.v)
    assert vtpv >= -1e-12


def test_algebraic_tra_a_equals_a_transpose():
    """tra_a = A^T."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    assert np.allclose(r.tra_a, r.a.T, rtol=1e-10)


def test_algebraic_tra_a_p_equals_a_transpose_p():
    """tra_a_p = A^T @ P."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    assert np.allclose(r.tra_a_p, r.tra_a @ r.p, rtol=1e-10)


def test_algebraic_t_equals_tra_a_p_l():
    """t = A^T @ P @ L."""
    t1 = _p1_target()
    t2 = _p2_target()
    r = _make_adjuster(t1, t2).calculate()
    t_check = r.tra_a_p @ r.l
    assert np.allclose(r.t, t_check, rtol=1e-10)


# ------------------------------------------------------------------ #
# (e) Redundancia 0
# ------------------------------------------------------------------ #

def test_redundancy_zero_four_points():
    """4 puntos distintos, 1 observacion c/u: 8 ec, 8 incognitas, red=0."""
    targets = [
        _p1_target(),
        _p2_target(),
        LsTarget("P3", P3_X, P3_Y, P3_DIST_UTM, P3_ACIMUT),
        LsTarget("P4", P4_X, P4_Y, P4_DIST_UTM, P4_ACIMUT),
    ]
    r = _make_adjuster(*targets).calculate()
    assert r.num_equations == 8
    assert r.num_unknowns == 8
    assert r.redundancy == 0
    assert r.desv_post == 0.0
    assert r.var_post == 0.0
    assert np.allclose(r.prec, 0.0)
    assert len(r.warnings) >= 1
    assert "Redundancia" in r.warnings[0]
    assert len(r.adjusted_coords) == 4
    assert all(coord[0] for coord in r.adjusted_coords)


# ------------------------------------------------------------------ #
# (f) Redundancia 2 (P2 observado dos veces)
# ------------------------------------------------------------------ #

def test_redundancy_two_with_duplicate_target():
    """4 puntos, P2 repetido: 5 obs = 10 ec, 8 incognitas, red=2."""
    targets = [
        _p1_target(),
        _p2_target(),
        _p2_target(),  # mismo target_name = misma incognita
        LsTarget("P3", P3_X, P3_Y, P3_DIST_UTM, P3_ACIMUT),
        LsTarget("P4", P4_X, P4_Y, P4_DIST_UTM, P4_ACIMUT),
    ]
    r = _make_adjuster(*targets).calculate()
    assert r.num_equations == 10
    assert r.num_unknowns == 8
    assert r.redundancy == 2
    assert r.desv_post > 0.0
    assert np.all(r.prec > 0.0)
    assert len(r.adjusted_coords) == 4


# ------------------------------------------------------------------ #
# (g) Errores
# ------------------------------------------------------------------ #

def test_no_targets_raises_value_error():
    """Lista vacia de observaciones -> ValueError."""
    with pytest.raises(ValueError, match="No hay observaciones"):
        _make_adjuster().calculate()


def test_station_co_located_raises():
    """Punto co-localizado con estacion (distancia nula) -> ValueError."""
    t = LsTarget("P0", 0.0, 0.0, 0.01, 100.0)
    with pytest.raises(ValueError, match="Distancia calculada nula"):
        _make_adjuster(t).calculate()


def test_zero_dist_utm_raises():
    """dist_utm = 0 -> ValueError."""
    t = LsTarget("P0", 100.0, 100.0, 0.0, 100.0)
    with pytest.raises(ValueError, match="Distancia UTM no positiva"):
        _make_adjuster(t).calculate()


# ------------------------------------------------------------------ #
# (h) Constantes y metadatos
# ------------------------------------------------------------------ #

def test_inter_conf_default():
    """INTER_CONF_DEFAULT debe coincidir con el Excel (z al 95%)."""
    assert INTER_CONF_DEFAULT == 1.9599639845400536


def test_result_inter_conf():
    """El resultado debe usar la inter_conf pasada al constructor."""
    custom = 2.5
    t = _p1_target()
    r = LeastSquaresAdjuster(
        station_x=STATION_X,
        station_y=STATION_Y,
        targets=[t],
        gon_r=GON_R,
        r_cc=R_CC,
        s_sexa_cc=S_SEXA_CC,
        prec_ang_etr=PREC_ANG_ETR,
        prec_dist_mm=PREC_DIST_MM,
        prec_dist_ppm=PREC_DIST_PPM,
        inter_conf=custom,
    ).calculate()
    assert r.inter_conf == custom


def test_single_target_has_adjusted_coords():
    """Con un solo punto, las coords ajustadas deben calcularse."""
    t = _p1_target()
    r = _make_adjuster(t).calculate()
    assert len(r.adjusted_coords) == 1
    name, ax, ay = r.adjusted_coords[0]
    assert name == "P1"
    assert isinstance(ax, float)
    assert isinstance(ay, float)


def test_sigma_dir_depends_on_prec_params():
    """Cambiar prec_ang_etr debe alterar sigma_dir."""
    t = _p1_target()
    r1 = _make_adjuster(t).calculate()
    adjuster2 = LeastSquaresAdjuster(
        STATION_X, STATION_Y, [t], GON_R, R_CC, S_SEXA_CC,
        prec_ang_etr=2.0, prec_dist_mm=0.8, prec_dist_ppm=1,
    )
    r2 = adjuster2.calculate()
    assert r2.sigma_dir[0] > r1.sigma_dir[0]


def test_sigma_dist_depends_on_prec_dist_params():
    """Cambiar prec_dist_mm debe alterar sigma_dist."""
    t = _p1_target()
    r1 = _make_adjuster(t).calculate()
    adjuster2 = LeastSquaresAdjuster(
        STATION_X, STATION_Y, [t], GON_R, R_CC, S_SEXA_CC,
        prec_ang_etr=0.5, prec_dist_mm=2.0, prec_dist_ppm=1,
    )
    r2 = adjuster2.calculate()
    assert r2.sigma_dist[0] > r1.sigma_dist[0]
