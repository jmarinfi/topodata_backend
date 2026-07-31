"""Helpers compartidos para los tests E2E.

Contiene un *driver* HTTP que recorre el flujo completo de la API
(proyecto → referencias → importación GKA → cálculo) y utilidades de
recálculo independiente (oráculo) para verificar los resultados.

Ninguna función aquí es un test; el módulo no sigue el patrón ``test_*`` por lo
que pytest no lo recoge.
"""

import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

# Constantes del modelo (Project / ImportSession) usadas por los oráculos.
_GON_R = math.pi / 200.0
_EARTH_RADIUS = 6378000.0
_R_CC = 2_000_000.0 / math.pi
_KT_COEF_REFR = 0.13
_S_SEXA_CC = 250.0 / 81.0
_PREC_ANG_ETR = 0.5
_K0_ADIM = 0.9996
# Convención del backend: C..M → hemisferio norte (sin false northing).
_NORTHERN_LETTERS = "CDEFGHJKLM"


# --------------------------------------------------------------------------- #
# Lectura de ficheros
# --------------------------------------------------------------------------- #
def read_gka(filename: str) -> str:
    """Lee un ``.gka`` de ``docs/`` como texto UTF-8."""
    return (DOCS / filename).read_text(encoding="utf-8")


def extract_reference_coords(gka_text: str) -> list[tuple[str, float, float, float]]:
    """Extrae las coordenadas de referencia (X/Y/Z) de un ``.gka``.

    Recorre las líneas de observación y devuelve los puntos que llevan
    coordenadas conocidas en las columnas 19/20/21 (EX/EY/EZ), p. ej. las
    referencias ``S01-R01`` del levantamiento S01. Devuelve
    ``(target_name, x=E, y=N, z)`` sin duplicados (primera aparición).
    """
    refs: dict[str, tuple[str, float, float, float]] = {}
    for line in gka_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        cols = line.split(",")
        if len(cols) <= 21:
            continue
        name = cols[1].strip()
        if not name:
            continue
        try:
            x = float(cols[19])
            y = float(cols[20])
            z = float(cols[21])
        except ValueError:
            continue
        if name not in refs:
            refs[name] = (name, x, y, z)
    return list(refs.values())


# --------------------------------------------------------------------------- #
# Driver HTTP (TestClient autenticado)
# --------------------------------------------------------------------------- #
def create_project(
    client,
    name: str = "Proyecto E2E",
    coordinate_system: str = "EPSG:25830",
    zona_utm: str = "30T",
) -> tuple[int, dict]:
    """Crea un proyecto y devuelve (id, body)."""
    r = client.post(
        "/api/v1/projects/",
        json={
            "name": name,
            "coordinate_system": coordinate_system,
            "zona_utm": zona_utm,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["id"], body


def add_references(client, project_id: int, refs) -> None:
    """Crea coordenadas de referencia.

    ``refs``: iterable de ``(target_name, x, y, z)``.
    """
    for name, x, y, z in refs:
        r = client.post(
            "/api/v1/reference-coordinates/",
            json={
                "target_name": name,
                "x": x,
                "y": y,
                "z": z,
                "project_id": project_id,
            },
        )
        assert r.status_code == 201, r.text


def import_gka(client, project_id: int, filename: str, content: str) -> dict:
    """Importa un ``.gka`` por el endpoint real (multipart) y devuelve el resultado."""
    r = client.post(
        f"/api/v1/projects/import_gka/{project_id}",
        files={"gka_file": (filename, content.encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 201, r.text
    return r.json()


def calculate_station(client, station_setup_id: int) -> list[dict]:
    """Dispara el pipeline completo (Cassini→k_utm→Z→desorientación→MMC)."""
    r = client.post(
        f"/api/v1/station-setups/{station_setup_id}/approximate-coordinates"
    )
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Getters de resultados
# --------------------------------------------------------------------------- #
def get_station(client, station_setup_id: int) -> dict:
    r = client.get(f"/api/v1/station-setups/{station_setup_id}")
    assert r.status_code == 200, r.text
    return r.json()


def get_raw_observations(client, station_setup_id: int) -> list[dict]:
    r = client.get(
        f"/api/v1/raw-observations/?station_setup_id={station_setup_id}"
    )
    assert r.status_code == 200, r.text
    return r.json()


def get_bessel(client, station_setup_id: int) -> list[dict]:
    r = client.get(
        f"/api/v1/bessel-observations/?station_setup_id={station_setup_id}"
    )
    assert r.status_code == 200, r.text
    return r.json()


def get_approx(client, station_setup_id: int) -> list[dict]:
    r = client.get(
        f"/api/v1/approximate-coordinates/by-station-setup/{station_setup_id}"
    )
    assert r.status_code == 200, r.text
    return r.json()


def get_adjusted(client, station_setup_id: int) -> list[dict]:
    r = client.get(
        f"/api/v1/adjusted-coordinates/by-station-setup/{station_setup_id}"
    )
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Oráculo: recálculo independiente del promedio Bessel (python puro)
# --------------------------------------------------------------------------- #
def recompute_bessel(raw_obs: list[dict]) -> dict:
    """Recalcula el promedio Bessel sin depender del backend.

    ``raw_obs``: lista de dicts con ``target_name``, ``circle`` (1=directo,
    2=inverso), ``hz_angle``, ``v_angle``, ``distance_geom`` (en gon / metros).

    Devuelve ``{target_name: {"hz_b", "v_b", "d_b"}}`` para los puntos con un
    par directo/inverso válido (v ≠ 0 y distancia ≠ 0).
    """
    direct: dict[str, list[dict]] = defaultdict(list)
    inverse: dict[str, list[dict]] = defaultdict(list)
    for o in raw_obs:
        if o["v_angle"] == 0 or o["distance_geom"] == 0:
            continue
        if o["circle"] == 1:
            direct[o["target_name"]].append(o)
        elif o["circle"] == 2:
            inverse[o["target_name"]].append(o)

    out: dict[str, dict[str, float]] = {}
    for name in direct:
        if name not in inverse:
            continue
        hzd = sum(o["hz_angle"] for o in direct[name]) / len(direct[name])
        hzi = sum(o["hz_angle"] for o in inverse[name]) / len(inverse[name])
        vd = sum(o["v_angle"] for o in direct[name]) / len(direct[name])
        vi = sum(o["v_angle"] for o in inverse[name]) / len(inverse[name])
        dd = sum(o["distance_geom"] for o in direct[name]) / len(direct[name])
        di = sum(o["distance_geom"] for o in inverse[name]) / len(inverse[name])

        hzb = (hzd + hzi + (-200.0 if hzd < 200.0 else 200.0)) / 2.0
        vb = vd - (vd + vi - 400.0) / 2.0
        db = (dd + di) / 2.0
        out[name] = {"hz_b": hzb, "v_b": vb, "d_b": db}
    return out


# --------------------------------------------------------------------------- #
# Oráculo: recálculo independiente de la radiación (coords aproximadas)
# --------------------------------------------------------------------------- #
def recompute_radiation(
    bessel_obs: list[dict],
    etr_x: float,
    etr_y: float,
    etr_z: float,
    k_utm: float,
    desorientacion: float,
    kt_coef_refr: float = _KT_COEF_REFR,
) -> dict[str, tuple[float, float, float]]:
    """Recalcula las coordenadas aproximadas (radiación) con la fórmula del Colab.

    ``bessel_obs``: lista de dicts con ``target_name``, ``hz_angle_bessel``,
    ``v_angle_bessel`` y ``distance_bessel`` (gon / metros).

    Devuelve ``{target_name: (x, y, z)}``. Reimplementación independiente de
    ``AproxCoordsAdjuster._calculate_coordenada_aproximada``.
    """
    out: dict[str, tuple[float, float, float]] = {}
    for b in bessel_obs:
        d = b["distance_bessel"]
        v = b["v_angle_bessel"]
        hz = b["hz_angle_bessel"]

        w_cc = d * _R_CC / _EARTH_RADIUS
        r_cc_v = kt_coef_refr * w_cc
        dist_hor = (
            d
            * math.sin((v - w_cc + r_cc_v) * _GON_R)
            / math.cos((w_cc / 2.0) * _GON_R)
        )
        dist_elip = dist_hor * _EARTH_RADIUS / (_EARTH_RADIUS + etr_z)
        dist_utm = dist_elip * k_utm

        acimut = hz + desorientacion
        if acimut > 400.0:
            acimut -= 400.0
        x = etr_x + dist_utm * math.sin(acimut * _GON_R)
        y = etr_y + dist_utm * math.cos(acimut * _GON_R)
        z = (
            d * math.cos(v * _GON_R)
            + (0.5 - kt_coef_refr) * d * d / _EARTH_RADIUS
            + etr_z
        )
        out[b["target_name"]] = (x, y, z)
    return out


# --------------------------------------------------------------------------- #
# Oráculos: etapas previas a la radiación (resección, k_utm, Z, desorientación)
# --------------------------------------------------------------------------- #
# Reimplementaciones independientes (python puro) de los cálculos del Colab /
# backend. Toman los mismos inputs que usa el pipeline y devuelven lo esperado.
def oracle_resection(
    refs: list[tuple[str, float, float, float]],
    hz_by_name: dict[str, float],
    gon_r: float = _GON_R,
) -> tuple[float, float]:
    """Inversa planimétrica de Cassini promediada sobre tríos."""
    pts = [(n, x, y) for (n, x, y, _z) in refs if n in hz_by_name]
    xs: list[float] = []
    ys: list[float] = []
    for p1, p2, p3 in combinations(pts, 3):
        (_n1, x1, y1), (_n2, x2, y2), (_n3, x3, y3) = p1, p2, p3
        lh1 = hz_by_name[p1[0]]
        lh2 = hz_by_name[p2[0]]
        lh3 = hz_by_name[p3[0]]
        try:
            alfa = (lh2 - lh1) * gon_r
            beta = (lh3 - lh2) * gon_r
            xa = x2 - x1 - (y2 - y1) / math.tan(alfa)
            xb = y2 - y1 + (x2 - x1) / math.tan(alfa)
            xc = x2 - x3 + (y2 - y3) / math.tan(beta)
            xd = y2 - y3 - (x2 - x3) / math.tan(beta)
            denom = (xa - xc) ** 2 + (xb - xd) ** 2
            xe = (xa * (xb - xd) - xb * (xa - xc)) / denom
            xs.append(x2 - xe * (xb - xd))
            ys.append(y2 + xe * (xa - xc))
        except (ZeroDivisionError, ValueError):
            continue
    return sum(xs) / len(xs), sum(ys) / len(ys)


def oracle_k_utm(
    etr_x: float,
    etr_y: float,
    zona_utm: str,
    a_elip: float,
    b_elip: float,
    f_elip: float,
    k_0_adim: float = _K0_ADIM,
) -> float:
    """Factor de escala puntual UTM (serie inversa → footpoint → k_prima)."""
    zone_letter = zona_utm.strip()[-1].upper()
    j8 = (etr_x - 500000.0) / k_0_adim
    if zone_letter in _NORTHERN_LETTERS:
        j9 = etr_y / k_0_adim
    else:
        j9 = (etr_y - 10000000.0) / k_0_adim

    b10 = f_elip * (2 - f_elip)
    b11 = (a_elip**2 - b_elip**2) / (b_elip**2)
    b16, b17 = b10**2, b10**3

    f21 = 1 + (3 / 4) * b10 + (45 / 64) * b16 + (175 / 256) * b17
    f22 = (3 / 4) * b10 + (15 / 16) * b16 + (525 / 512) * b17
    f23 = (15 / 64) * b16 + (105 / 256) * b17
    f24 = (35 / 512) * b17

    i21 = f21 * a_elip * (1 - b10)
    i22 = (f22 / 2) * a_elip * (1 - b10)
    i23 = (f23 / 4) * a_elip * (1 - b10)
    i24 = (f24 / 6) * a_elip * (1 - b10)

    o3 = j9 / i21
    o4 = (j9 + i22 * math.sin(2 * o3) - i23 * math.sin(4 * o3) + i24 * math.sin(6 * o3)) / i21
    o5 = (j9 + i22 * math.sin(2 * o4) - i23 * math.sin(4 * o4) + i24 * math.sin(6 * o4)) / i21
    o6 = (j9 + i22 * math.sin(2 * o5) - i23 * math.sin(4 * o5) + i24 * math.sin(6 * o5)) / i21

    sin_o6, cos_o6, tan_o6 = math.sin(o6), math.cos(o6), math.tan(o6)
    j14 = (a_elip * (1 - b10)) / (1 - b10 * sin_o6**2) ** (3 / 2)
    j13 = a_elip / math.sqrt(1 - b10 * sin_o6**2)

    b14 = b11 * cos_o6**2
    b18, b19 = b14**2, b14**3

    k_prima = (
        1
        + (j8**2) / (2 * j14 * j13)
        + (j8**4)
        / (24 * j13**4)
        * (
            1
            + 6 * b14
            + 9 * b18
            - 24 * tan_o6**2 * b18
            + 4 * b19
            - 24 * tan_o6**2 * b19
        )
    )
    return k_prima * k_0_adim


def oracle_z_est(
    refs: list[tuple[str, float, float, float]],
    v_by_name: dict[str, float],
    target_height_by_name: dict[str, float],
    etr_x: float,
    etr_y: float,
    k_utm: float,
    station_height: float | None,
    gon_r: float = _GON_R,
    earth_radius: float = _EARTH_RADIUS,
    s_sexa_cc: float = _S_SEXA_CC,
    kt_coef_refr: float = _KT_COEF_REFR,
    prec_ang_etr: float = _PREC_ANG_ETR,
) -> float:
    """Cota de la estación (ZEST) en dos pasadas (horizonte → elipsoide)."""
    usable = [
        (n, x, y, z)
        for (n, x, y, z) in refs
        if n in v_by_name and n in target_height_by_name
    ]
    instrument = station_height or 0.0
    dist_red: dict[str, float] = {}

    z_prima: list[float] = []
    for _n, x, y, z in usable:
        dist_calculada = math.hypot(x - etr_x, y - etr_y)
        dist_reducida = dist_calculada / k_utm
        dist_red[_n] = dist_reducida
        v = v_by_name[_n]
        m = target_height_by_name[_n]
        delta_z = (
            dist_reducida * math.cos(v * gon_r)
            + (instrument - m)
            + (0.5 - kt_coef_refr) * dist_reducida**2 / earth_radius
        )
        z_prima.append(z - delta_z)
    z_prima_mean = sum(z_prima) / len(z_prima)

    z_refs: list[float] = []
    for _n, _x, _y, z in usable:
        dist_reducida = dist_red[_n]
        dist_red_elip = dist_reducida * (z_prima_mean + earth_radius) / earth_radius
        v = v_by_name[_n]
        m = target_height_by_name[_n]
        delta_z = (
            dist_red_elip * math.cos(v * gon_r)
            + (instrument - m)
            + (0.5 - kt_coef_refr) * dist_red_elip**2 / earth_radius
        )
        z_refs.append(z - delta_z)

    omega = (prec_ang_etr * s_sexa_cc) ** 2
    return (sum(z_refs) / omega) / ((1 / omega) * len(z_refs))


def oracle_desorientacion(
    refs: list[tuple[str, float, float, float]],
    hz_by_name: dict[str, float],
    etr_x: float,
    etr_y: float,
    gon_r: float = _GON_R,
) -> float:
    """Desorientación media (acimut − hz_bessel, normalizado a [0, 400) gon)."""
    des = []
    for n, x, y, _z in refs:
        if n not in hz_by_name:
            continue
        acimut = math.atan2(x - etr_x, y - etr_y) / gon_r
        acimut = acimut if acimut > 0.0 else acimut + 400.0
        d = acimut - hz_by_name[n]
        d = d if d > 0.0 else d + 400.0
        des.append(d)
    return sum(des) / len(des)
