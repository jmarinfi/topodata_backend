import math
from dataclasses import dataclass

from api.schemas import BesselObservationResponse, ReferenceCoordinateResponse


@dataclass
class DesorientacionResult:
    """Resultado del cálculo de la desorientación del estacionamiento."""

    desorientacion: float
    combinations: int
    """Número de referencias observadas que contribuyeron a la media."""


@dataclass
class RadiacionResult:
    """Resultado de la radiación de una coordenada aproximada.

    Incluye valores intermedios para validación contra los oracles del Excel.
    """

    target_name: str
    x: float
    y: float
    z: float
    # Intermedios para tests
    w_cc: float
    r_cc: float
    dist_hor: float
    dist_elip: float
    dist_utm: float
    acimut: float


class ApproximateCoordinateCalculator:
    """Desorientación del estacionamiento y coordenadas aproximadas (radiación).

    La desorientación es puerto del ``AproxCoordsAdjuster`` de
    ``docs/ajustes_topografia.py`` (B2.5). La radiación (B2.6) sigue los
    Excel v2 (``Cálculo distancias reducidas v2.xlsx`` y ``Cálculo coord
    aproximadas v2.xlsx``): el Colab y el Excel antiguo mezclaban cc sobre
    gones en la reducción al horizonte.
    """

    @staticmethod
    def calculate_desorientacion(
        etr_x: float,
        etr_y: float,
        references: list[ReferenceCoordinateResponse],
        bessel_observations: list[BesselObservationResponse],
        gon_r: float,
    ) -> DesorientacionResult:
        """Desorientación (ε) media del estacionamiento.

        Para cada referencia observada se calcula el acimut topográfico entre
        la estación y la referencia y se le resta el ángulo horizontal Bessel;
        la media de esas diferencias (normalizadas a [0, 400) gon) es la
        desorientación del estacionamiento.

        Nota: el paso **rad→gon** usa ``1 / gon_r`` (= 200/π). El borrador del
        Colab multiplica por ``gon_r`` (factor inverso, gon→rad); aquí se usa
        el factor correcto, validado contra el Excel (acimut de C55-R-01E-C =
        351.5897 gon).
        """
        hz_by_target = {
            obs.target_name: obs.hz_angle_bessel for obs in bessel_observations
        }

        # Sólo las referencias observadas (con ángulo horizontal Bessel).
        pairs = [
            (ref, hz_by_target[ref.target_name])
            for ref in references
            if ref.target_name in hz_by_target
        ]
        if not pairs:
            raise ValueError(
                "No hay referencias observadas (con ángulo horizontal Bessel) "
                "para calcular la desorientación."
            )

        desorientaciones: list[float] = []
        for ref, hz_bessel in pairs:
            acimut = math.atan2(ref.x - etr_x, ref.y - etr_y) / gon_r
            acimut = acimut if acimut > 0.0 else acimut + 400.0

            desorientacion = acimut - hz_bessel
            desorientacion = (
                desorientacion if desorientacion > 0.0 else desorientacion + 400.0
            )
            desorientaciones.append(desorientacion)

        return DesorientacionResult(
            desorientacion=sum(desorientaciones) / len(desorientaciones),
            combinations=len(desorientaciones),
        )

    # ------------------------------------------------------------------ #
    # Radiación: coordenadas aproximadas (B2.6)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_radiacion(
        bessel: BesselObservationResponse,
        etr_x: float,
        etr_y: float,
        etr_z: float,
        k_utm: float,
        desorientacion: float,
        gon_r: float,
        earth_radius: float,
        r_cc: float,
        kt_coef_refr: float,
        instrument_height: float = 0.0,
        target_height: float = 0.0,
    ) -> RadiacionResult:
        """Radiación de una única observación Bessel → coordenada aproximada.

        Puerto de la columna I de ``Cálculo distancias reducidas v2.xlsx`` y
        de las columnas H-L de ``Cálculo coord aproximadas v2.xlsx`` (el
        ``_calculate_coordenada_aproximada`` del Colab y el Excel antiguo
        sumaban w y r en cc sobre un ángulo vertical en gon).
        Calcula las coordenadas (x, y, z) de un punto observado a partir de
        la posición de la estación, el factor de escala UTM, la desorientación
        y los ángulos/distancias Bessel.

        Parameters
        ----------
        bessel:
            Observación Bessel del punto a radiar.
        etr_x, etr_y, etr_z:
            Coordenadas UTM de la estación total.
        k_utm:
            Factor de escala puntual de la proyección UTM en la estación.
        desorientacion:
            Desorientación del estacionamiento (ε) en gon.
        gon_r:
            Factor de conversión gon → radianes (π/200).
        earth_radius:
            Radio medio de la Tierra (m).
        r_cc:
            Factor de conversión radianes → cc (2000000/π).
        kt_coef_refr:
            Coeficiente de refracción (valor por defecto: 0.13).
        instrument_height:
            altura del instrumento i (m).
        target_height:
            altura de mira m (m).
        """
        d = bessel.distance_bessel
        v = bessel.v_angle_bessel
        hz = bessel.hz_angle_bessel

        # Corrección por curvatura y refracción (en cc).
        w_cc = d * r_cc / earth_radius
        r_cc_val = kt_coef_refr * w_cc

        # Distancia reducida al horizonte de la estación. w y r están en cc:
        # 1 gon = 10000 cc (Excel v2, col. I).
        dist_hor = (
            d
            * math.sin((v + (r_cc_val - w_cc) / 10000.0) * gon_r)
            / math.cos((w_cc / 20000.0) * gon_r)
        )

        # Reducción al elipsoide.
        dist_elip = dist_hor * earth_radius / (earth_radius + etr_z)

        # Paso a la proyección UTM.
        dist_utm = dist_elip * k_utm

        # Acimut topográfico (hz + desorientación), normalizado a [0, 400).
        acimut = hz + desorientacion
        acimut = acimut - 400.0 if acimut > 400.0 else acimut

        # Coordenadas planimétricas (radiación).
        x = etr_x + dist_utm * math.sin(acimut * gon_r)
        y = etr_y + dist_utm * math.cos(acimut * gon_r)

        # Cota del punto: desnivel + corrección curvatura/refracción + i − m.
        z = (
            d * math.cos(v * gon_r)
            + (0.5 - kt_coef_refr) * d**2 / earth_radius
            + etr_z
            + instrument_height
            - target_height
        )

        return RadiacionResult(
            target_name=bessel.target_name,
            x=x,
            y=y,
            z=z,
            w_cc=w_cc,
            r_cc=r_cc_val,
            dist_hor=dist_hor,
            dist_elip=dist_elip,
            dist_utm=dist_utm,
            acimut=acimut,
        )

    @staticmethod
    def calculate_all_radiaciones(
        bessel_observations: list[BesselObservationResponse],
        etr_x: float,
        etr_y: float,
        etr_z: float,
        k_utm: float,
        desorientacion: float,
        gon_r: float,
        earth_radius: float,
        r_cc: float,
        kt_coef_refr: float,
        instrument_height: float = 0.0,
        target_height_by_target: dict[str, float] | None = None,
    ) -> list[RadiacionResult]:
        """Radiación de todas las observaciones Bessel de un estacionamiento.

        Devuelve una coordenada aproximada por cada observación Bessel.
        ``instrument_height`` es la altura de instrumento (i) común y
        ``target_height_by_target`` da la altura de mira (m) por objetivo
        (0 si falta), ambas para la cota.
        """
        heights = target_height_by_target or {}
        return [
            ApproximateCoordinateCalculator.calculate_radiacion(
                bessel=b,
                etr_x=etr_x,
                etr_y=etr_y,
                etr_z=etr_z,
                k_utm=k_utm,
                desorientacion=desorientacion,
                gon_r=gon_r,
                earth_radius=earth_radius,
                r_cc=r_cc,
                kt_coef_refr=kt_coef_refr,
                instrument_height=instrument_height,
                target_height=heights.get(b.target_name, 0.0),
            )
            for b in bessel_observations
        ]
