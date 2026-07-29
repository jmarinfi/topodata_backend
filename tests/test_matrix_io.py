import io
import math

import numpy as np
import pytest

from services.calculations.least_squares_adjuster import (
    LeastSquaresAdjuster,
    LsTarget,
)
from services.calculations.matrix_io import (
    from_bytes,
    scalar_from_bytes,
    scalar_to_bytes,
    to_bytes,
)

GON_R = math.pi / 200.0
R_CC = 2000000.0 / math.pi
S_SEXA_CC = 250.0 / 81.0


def _make_result():
    """Resultado MMC con redundancia > 0 (P2 observado dos veces)."""
    targets = [
        LsTarget("P1", -127.4318, 38.99909, 133.26547, 318.92),
        LsTarget("P2", 80.0, 30.0, 87.39099, 69.444),
        LsTarget("P2", 80.0, 30.0, 87.39099, 69.444),  # duplicado
    ]
    return LeastSquaresAdjuster(
        station_x=0.0,
        station_y=0.0,
        targets=targets,
        gon_r=GON_R,
        r_cc=R_CC,
        s_sexa_cc=S_SEXA_CC,
        prec_ang_etr=0.5,
        prec_dist_mm=0.8,
        prec_dist_ppm=1.0,
    ).calculate()


# ------------------------------------------------------------------ #
# (a) Round-trip matriz 2D float
# ------------------------------------------------------------------ #

def test_roundtrip_2d_float():
    m = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
    restored = from_bytes(to_bytes(m))
    assert restored.shape == m.shape
    assert restored.dtype == m.dtype
    assert np.allclose(restored, m)


# ------------------------------------------------------------------ #
# (b) Round-trip vector 1D
# ------------------------------------------------------------------ #

def test_roundtrip_1d():
    v = np.array([1.5, -2.3, 0.0, 7.8])
    restored = from_bytes(to_bytes(v))
    assert restored.shape == v.shape
    assert np.allclose(restored, v)


# ------------------------------------------------------------------ #
# (c) dtype preservado en enteros
# ------------------------------------------------------------------ #

def test_dtype_int_preserved():
    a = np.array([-1, 0, 42, 100], dtype=np.int32)
    restored = from_bytes(to_bytes(a))
    assert restored.dtype == np.int32
    assert np.array_equal(restored, a)


# ------------------------------------------------------------------ #
# (d) Round-trip array vacio
# ------------------------------------------------------------------ #

def test_roundtrip_empty():
    a = np.array([])
    restored = from_bytes(to_bytes(a))
    assert restored.shape == (0,)
    assert restored.dtype == a.dtype
    assert np.array_equal(restored, a)


# ------------------------------------------------------------------ #
# (e) to_bytes devuelve bytes
# ------------------------------------------------------------------ #

def test_to_bytes_returns_bytes():
    b = to_bytes(np.array([1, 2, 3]))
    assert isinstance(b, bytes)
    assert len(b) > 0


# ------------------------------------------------------------------ #
# (f) Escalar float
# ------------------------------------------------------------------ #

def test_scalar_float_roundtrip():
    original = 3.14
    result = scalar_from_bytes(scalar_to_bytes(original))
    assert result == pytest.approx(original)
    assert isinstance(result, float)


# ------------------------------------------------------------------ #
# (g) Escalar int
# ------------------------------------------------------------------ #

def test_scalar_int_roundtrip():
    original = 8
    result = scalar_from_bytes(scalar_to_bytes(original))
    assert result == original
    assert isinstance(result, int)


# ------------------------------------------------------------------ #
# (h) Keystone end-to-end: serializar 12 arrays + 5 escalares
# ------------------------------------------------------------------ #

def test_keystone_all_matrices_roundtrip():
    r = _make_result()
    assert r.redundancy > 0

    # 12 arrays
    arrays = {
        "v": r.v,
        "a": r.a,
        "tra_a": r.tra_a,
        "p": r.p,
        "tra_a_p": r.tra_a_p,
        "x": r.x,
        "l": r.l,
        "n": r.n,
        "inver_n": r.inver_n,
        "t": r.t,
        "tra_v_p": r.tra_v_p,
        "prec": r.prec,
    }
    for name, arr in arrays.items():
        restored = from_bytes(to_bytes(arr))
        assert restored.shape == arr.shape, f"{name}: shape mismatch"
        assert restored.dtype == arr.dtype, f"{name}: dtype mismatch"
        assert np.allclose(restored, arr), f"{name}: values mismatch"

    # 5 escalares
    assert scalar_from_bytes(scalar_to_bytes(r.desv_post)) == pytest.approx(r.desv_post)
    assert scalar_from_bytes(scalar_to_bytes(r.var_post)) == pytest.approx(r.var_post)
    assert scalar_from_bytes(scalar_to_bytes(r.num_equations)) == r.num_equations
    assert isinstance(scalar_from_bytes(scalar_to_bytes(r.num_equations)), int)
    assert scalar_from_bytes(scalar_to_bytes(r.num_unknowns)) == r.num_unknowns
    assert isinstance(scalar_from_bytes(scalar_to_bytes(r.num_unknowns)), int)
    assert scalar_from_bytes(scalar_to_bytes(r.inter_conf)) == pytest.approx(r.inter_conf)


# ------------------------------------------------------------------ #
# (i) from_bytes rechaza pickle por seguridad
# ------------------------------------------------------------------ #

def test_from_bytes_rejects_pickle():
    """from_bytes usa allow_pickle=False: un payload que exige pickle debe rechazarse."""
    buf = io.BytesIO()
    np.save(buf, np.array(["x"], dtype=object), allow_pickle=True)
    with pytest.raises(ValueError):
        from_bytes(buf.getvalue())


def test_scalar_roundtrip_preserves_negative():
    original = -42.0
    result = scalar_from_bytes(scalar_to_bytes(original))
    assert result == pytest.approx(original)
    assert isinstance(result, float)
