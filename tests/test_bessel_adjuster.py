"""Corrección numérica del BesselAdjuster con un par sintético directo+inverso.

Valores elegidos (gon):
  directo  (círculo 1): hz=50,  v=310, dist=100
  inverso  (círculo 2): hz=250, v=110, dist=102

Esperado (de la formulación de bessel_adjuster.adjust_bessel):
  hz_bessel   = (50 + 250 - 200) / 2        = 50
  v_bessel    = 310 - (310 + 110 - 400) / 2 = 300
  dist_bessel = mean(100, 102)              = 101
  hz_delta    = (250 - 50 - 200) / 2        = 0
  v_delta     = (310 - 300) * 2             = 20
  dist_delta  = (101 - 100) * 2             = 2
"""

import pytest

from api.schemas import RawObservationResponse, StationSetupResponse
from services.calculations.bessel_adjuster import BesselAdjuster


def _obs(obs_id: int, circle: int, hz: float, v: float, dist: float):
    return RawObservationResponse(
        id=obs_id,
        station_setup_id=1,
        target_name="T1",
        target_number=1,
        circle=circle,
        hz_angle=hz,
        v_angle=v,
        distance_geom=dist,
    )


def _station():
    return StationSetupResponse(id=1, import_session_id=1, station_name="S1")


def test_bessel_synthetic_pair():
    result = BesselAdjuster(
        _station(),
        [_obs(1, 1, 50.0, 310.0, 100.0), _obs(2, 2, 250.0, 110.0, 102.0)],
    ).adjust_bessel()

    assert len(result) == 1
    b = result[0]
    assert b.hz_angle_bessel == pytest.approx(50.0)
    assert b.v_angle_bessel == pytest.approx(300.0)
    assert b.distance_bessel == pytest.approx(101.0)
    assert b.hz_angle_delta == pytest.approx(0.0)
    assert b.v_angle_delta == pytest.approx(20.0)
    assert b.distance_delta == pytest.approx(2.0)


def test_bessel_without_inverse_pair_raises():
    # Sólo círculo directo: sin par inverso → el adjuster aborta (ValueError).
    with pytest.raises(ValueError):
        BesselAdjuster(_station(), [_obs(1, 1, 50.0, 310.0, 100.0)]).adjust_bessel()
