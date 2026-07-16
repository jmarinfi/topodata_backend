import logging
import math
from dataclasses import dataclass
from itertools import combinations

from api.schemas import (
    BesselObservationResponse,
    RawObservationResponse,
    ReferenceCoordinateResponse,
)

logger = logging.getLogger(__name__)

# Bandas UTM válidas; C..M hemisferio norte, N..X sur.
_UTM_ZONE_LETTERS = "CDEFGHJKLMNPQRSTUVWX"
_NORTHERN_LETTERS = "CDEFGHJKLM"


@dataclass
class ResectionResult:
    """Resultado de la inversa planimétrica de la estación."""

    etr_x: float
    etr_y: float
    combinations: int
    """Número de tríos válidos que contribuyeron a la media."""


@dataclass
class ZEstResult:
    """Resultado del cálculo de la cota de la estación."""

    z_est: float
    """Cota final (ZEST) tras la reducción al elipsoide."""
    z_prima_mean: float
    """Cota media de la primera pasada (reducción al horizonte)."""
    combinations: int
    """Número de referencias que contribuyeron a la media."""


class StationPositionCalculator:
    """Cálculos de posicionamiento de la estación total.

    Equivalente al ``KUTMAdjuster`` de ``docs/ajustes_topografia.py``. Agrupa:

    - la **inversa planimétrica de Cassini** → coordenadas ``etr_x``, ``etr_y``
      (método de instancia, necesita las referencias y observaciones);
    - el **factor de escala UTM** ``k_utm`` (método estático, función pura de
      la posición, la zona UTM y el elipsoide);
    - la **cota de la estación** ``etr_z`` (ZEST) por ángulos verticales
      (método estático).
    """

    MIN_REFERENCES = 3

    def __init__(
        self,
        references: list[ReferenceCoordinateResponse],
        bessel_observations: list[BesselObservationResponse],
        gon_r: float,
    ) -> None:
        self.gon_r = gon_r

        # Sólo sirven para la inversa las referencias que además están
        # observadas (tienen un ángulo horizontal Bessel).
        hz_by_target = {
            obs.target_name: obs.hz_angle_bessel for obs in bessel_observations
        }
        self._hz_by_target = hz_by_target
        self._references = [
            ref for ref in references if ref.target_name in hz_by_target
        ]

        if len(self._references) < self.MIN_REFERENCES:
            raise ValueError(
                "Se necesitan al menos 3 puntos de referencia observados "
                "(con ángulo horizontal Bessel) para la inversa planimétrica."
            )

    # ------------------------------------------------------------------ #
    # Inversa planimétrica de Cassini
    # ------------------------------------------------------------------ #

    def _cassini(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        lh1: float,
        lh2: float,
        lh3: float,
    ) -> tuple[float, float]:
        """Inversa planimétrica para un trío de puntos.

        ``lh1``/``lh2``/``lh3`` son los ángulos horizontales (gon) observados
        desde el teodolito hacia los puntos 1/2/3. Devuelve las coordenadas
        (x, y) del teodolito.
        """
        angulo_alfa = (lh2 - lh1) * self.gon_r
        angulo_beta = (lh3 - lh2) * self.gon_r

        x_a = x2 - x1 - (y2 - y1) / math.tan(angulo_alfa)
        x_b = y2 - y1 + (x2 - x1) / math.tan(angulo_alfa)
        x_c = x2 - x3 + (y2 - y3) / math.tan(angulo_beta)
        x_d = y2 - y3 - (x2 - x3) / math.tan(angulo_beta)
        x_e = (x_a * (x_b - x_d) - x_b * (x_a - x_c)) / (
            (x_a - x_c) ** 2 + (x_b - x_d) ** 2
        )

        x_teod = x2 - x_e * (x_b - x_d)
        y_teod = y2 + x_e * (x_a - x_c)
        return (x_teod, y_teod)

    def calculate_resection(self) -> ResectionResult:
        """Inversa planimétrica promediada sobre las combinaciones de 3."""
        xs: list[float] = []
        ys: list[float] = []
        skipped = 0

        for p1, p2, p3 in combinations(self._references, 3):
            try:
                x, y = self._cassini(
                    p1.x,
                    p1.y,
                    p2.x,
                    p2.y,
                    p3.x,
                    p3.y,
                    self._hz_by_target[p1.target_name],
                    self._hz_by_target[p2.target_name],
                    self._hz_by_target[p3.target_name],
                )
            except (ZeroDivisionError, ValueError):
                # Trío degenerado (ángulo incluido ~0/200 gon o colinear):
                # se descarta para no corromper la media.
                skipped += 1
                continue
            xs.append(x)
            ys.append(y)

        if not xs:
            raise ValueError(
                "No se ha podido calcular la inversa planimétrica: ningún "
                "trío de referencias produce una geometría válida."
            )

        logger.debug(
            "Inversa Cassini: %d tríos válidos, %d descartados.", len(xs), skipped
        )
        return ResectionResult(
            etr_x=sum(xs) / len(xs),
            etr_y=sum(ys) / len(ys),
            combinations=len(xs),
        )

    # ------------------------------------------------------------------ #
    # Factor de escala UTM (k_utm)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_k_utm(
        etr_x: float,
        etr_y: float,
        zona_utm: str,
        a_elip: float,
        b_elip: float,
        f_elip: float,
        k_0_adim: float,
    ) -> float:
        """Factor de escala puntual de la proyección UTM en la estación.

        Puerto de ``KUTMAdjuster.calculate_k_utm``: serie inversa UTM →
        latitud de «footpoint» (O6) y, desde ella, factor de escala
        ``k_prima``, multiplicado por ``k_0_adim`` (0.9996).
        """
        zona_utm = (zona_utm or "").strip()
        if len(zona_utm) < 2:
            raise ValueError(f"Zona UTM no válida: {zona_utm!r}")

        zone_letter = zona_utm[-1].upper()
        try:
            zone_number = int(zona_utm[:-1])
        except ValueError as exc:
            raise ValueError(
                f"Número de zona UTM no válido: {zona_utm!r}"
            ) from exc
        if zone_letter not in _UTM_ZONE_LETTERS:
            raise ValueError(f"Letra de zona UTM no válida: {zone_letter!r}")

        # Coordenadas reducidas al meridiano central (sin k_0).
        j8 = (etr_x - 500000.0) / k_0_adim
        if zone_letter in _NORTHERN_LETTERS:
            j9 = etr_y / k_0_adim
        else:
            j9 = (etr_y - 10000000.0) / k_0_adim

        # Excentricidades y series del elipsoide.
        b10 = f_elip * (2 - f_elip)  # e² (primera excentricidad)
        b11 = (a_elip**2 - b_elip**2) / (b_elip**2)  # e'² (segunda)
        b16 = b10**2
        b17 = b10**3

        f21 = 1 + (3 / 4) * b10 + (45 / 64) * b16 + (175 / 256) * b17
        f22 = (3 / 4) * b10 + (15 / 16) * b16 + (525 / 512) * b17
        f23 = (15 / 64) * b16 + (105 / 256) * b17
        f24 = (35 / 512) * b17

        i21 = f21 * a_elip * (1 - b10)
        i22 = (f22 / 2) * a_elip * (1 - b10)
        i23 = (f23 / 4) * a_elip * (1 - b10)
        i24 = (f24 / 6) * a_elip * (1 - b10)

        # Latitud del footpoint por iteración de la serie (O3 → O6).
        o3 = j9 / i21
        o4 = (j9 + i22 * math.sin(2 * o3) - i23 * math.sin(4 * o3) + i24 * math.sin(6 * o3)) / i21
        o5 = (j9 + i22 * math.sin(2 * o4) - i23 * math.sin(4 * o4) + i24 * math.sin(6 * o4)) / i21
        o6 = (j9 + i22 * math.sin(2 * o5) - i23 * math.sin(4 * o5) + i24 * math.sin(6 * o5)) / i21

        sin_o6 = math.sin(o6)
        cos_o6 = math.cos(o6)
        tan_o6 = math.tan(o6)

        j14 = (a_elip * (1 - b10)) / (1 - b10 * (sin_o6**2)) ** (3 / 2)
        j13 = a_elip / math.sqrt(1 - b10 * (sin_o6**2))

        b14 = b11 * (cos_o6**2)
        b18 = b14**2
        b19 = b14**3

        k_prima = (
            1
            + (j8**2) / (2 * j14 * j13)
            + (j8**4)
            / (24 * j13**4)
            * (
                1
                + 6 * b14
                + 9 * b18
                - 24 * (tan_o6**2) * b18
                + 4 * b19
                - 24 * (tan_o6**2) * b19
            )
        )
        return k_prima * k_0_adim

    # ------------------------------------------------------------------ #
    # Cota de la estación (etr_z / ZEST)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_z_est(
        etr_x: float,
        etr_y: float,
        k_utm: float,
        references: list[ReferenceCoordinateResponse],
        bessel_observations: list[BesselObservationResponse],
        raw_observations: list[RawObservationResponse],
        station_height: float | None,
        gon_r: float,
        earth_radius: float,
        s_sexa_cc: float,
        kt_coef_refr: float,
        prec_ang_etr: float,
    ) -> ZEstResult:
        """Cota de la estación por ángulos verticales (ZEST).

        Puerto de ``KUTMAdjuster.calculate_z_est``. Para cada referencia
        observada se estima la cota de la estación a partir de su cota conocida,
        la distancia reducida y el ángulo vertical Bessel, en dos pasadas
        (reducción al horizonte → ``Z'``, y al elipsoide → ``Z''``) y se
        promedian.

        ``station_height`` es la altura de instrumento (``i``); la altura de
        señal (``m``) se toma de ``raw_observations.target_height``. Ambas se
        tratan como 0 si faltan, igual que en el Colab.
        """
        v_angle_by_target = {
            obs.target_name: obs.v_angle_bessel for obs in bessel_observations
        }
        target_height_by_target = {
            obs.target_name: (obs.target_height or 0.0) for obs in raw_observations
        }
        instrument_height = station_height or 0.0

        # Sólo referencias con ángulo vertical y altura de señal conocidos.
        usable = [
            ref
            for ref in references
            if ref.target_name in v_angle_by_target
            and ref.target_name in target_height_by_target
        ]
        if not usable:
            raise ValueError(
                "No hay referencias con ángulo vertical Bessel y altura de "
                "señal para calcular la cota de la estación."
            )

        dist_reducida_by_target: dict[str, float] = {}

        # Pasada 1: reducción al horizonte → Z'.
        z_prima_refs: list[float] = []
        for ref in usable:
            dist_calculada = math.hypot(ref.x - etr_x, ref.y - etr_y)
            dist_reducida = dist_calculada / k_utm
            dist_reducida_by_target[ref.target_name] = dist_reducida

            v_angle = v_angle_by_target[ref.target_name]
            target_height = target_height_by_target[ref.target_name]
            delta_z = (
                dist_reducida * math.cos(v_angle * gon_r)
                + (instrument_height - target_height)
                + (0.5 - kt_coef_refr) * (dist_reducida**2) / earth_radius
            )
            z_prima_refs.append(ref.z - delta_z)

        z_prima_mean = sum(z_prima_refs) / len(z_prima_refs)

        # Pasada 2: reducción al elipsoide (con la cota media) → Z''.
        z_refs: list[float] = []
        for ref in usable:
            dist_reducida = dist_reducida_by_target[ref.target_name]
            dist_red_elipsoide = (
                dist_reducida * (z_prima_mean + earth_radius) / earth_radius
            )
            v_angle = v_angle_by_target[ref.target_name]
            target_height = target_height_by_target[ref.target_name]
            delta_z = (
                dist_red_elipsoide * math.cos(v_angle * gon_r)
                + (instrument_height - target_height)
                + (0.5 - kt_coef_refr) * (dist_red_elipsoide**2) / earth_radius
            )
            z_refs.append(ref.z - delta_z)

        # El Colab pondera por σ(α)² = (prec_ang_etr · s_sexa_cc)²; al ser el
        # peso común a todas las referencias, el promedio ponderado equivale a
        # la media aritmética. Se mantiene la formulación fiel al Colab.
        omega_alpha_cc = (prec_ang_etr * s_sexa_cc) ** 2
        z_est = (sum(z_refs) / omega_alpha_cc) / (
            (1 / omega_alpha_cc) * len(z_refs)
        )

        return ZEstResult(
            z_est=z_est, z_prima_mean=z_prima_mean, combinations=len(z_refs)
        )
