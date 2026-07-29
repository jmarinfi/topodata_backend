import logging
import math
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

INTER_CONF_DEFAULT = 1.9599639845400536


@dataclass
class LsTarget:
    """Observación de un punto visado para el ajuste MMC."""

    target_name: str
    approx_x: float
    approx_y: float
    dist_utm: float
    acimut_observado: float
    prec_senal: float = 0.0
    prec_punteria_cc: float = 3.09


@dataclass
class LeastSquaresResult:
    sigma_dir: np.ndarray = field(default_factory=lambda: np.array([]))
    sigma_dist: np.ndarray = field(default_factory=lambda: np.array([]))
    a: np.ndarray = field(default_factory=lambda: np.array([]))
    tra_a: np.ndarray = field(default_factory=lambda: np.array([]))
    p: np.ndarray = field(default_factory=lambda: np.array([]))
    tra_a_p: np.ndarray = field(default_factory=lambda: np.array([]))
    l: np.ndarray = field(default_factory=lambda: np.array([]))
    n: np.ndarray = field(default_factory=lambda: np.array([]))
    inver_n: np.ndarray = field(default_factory=lambda: np.array([]))
    t: np.ndarray = field(default_factory=lambda: np.array([]))
    x: np.ndarray = field(default_factory=lambda: np.array([]))
    v: np.ndarray = field(default_factory=lambda: np.array([]))
    tra_v_p: np.ndarray = field(default_factory=lambda: np.array([]))
    num_equations: int = 0
    num_unknowns: int = 0
    redundancy: int = 0
    var_post: float = 0.0
    desv_post: float = 0.0
    inter_conf: float = INTER_CONF_DEFAULT
    prec: np.ndarray = field(default_factory=lambda: np.array([]))
    adjusted_coords: list[tuple[str, float, float]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class LeastSquaresAdjuster:
    """Ajuste por mínimos cuadrados (MMC) de direcciones + distancias.

    Toma un conjunto de observaciones (dirección y distancia a puntos visados
    desde una estación fija) y refina las coordenadas aproximadas de esos
    puntos mediante el ajuste paramétrico clásico::

        A → Aᵀ → P → AᵀP → L → N=AᵀPA → N⁻¹ → t=AᵀPL → x=N⁻¹t
        → v=Ax−L → vᵀPv → σ̂², σ̂ → precisiones y coords ajustadas.

    La estación permanece fija en su posición inversa; todas las incógnitas
    son los ``dx, dy`` de los puntos visados.
    """

    def __init__(
        self,
        station_x: float,
        station_y: float,
        targets: list[LsTarget],
        gon_r: float,
        r_cc: float,
        s_sexa_cc: float,
        prec_ang_etr: float,
        prec_dist_mm: float,
        prec_dist_ppm: float,
        inter_conf: float = INTER_CONF_DEFAULT,
    ) -> None:
        if not targets:
            raise ValueError("No hay observaciones para el ajuste MMC.")

        self.station_x = station_x
        self.station_y = station_y
        self.targets = targets
        self.gon_r = gon_r
        self.r_cc = r_cc
        self.s_sexa_cc = s_sexa_cc
        self.prec_ang_etr = prec_ang_etr
        self.prec_dist_mm = prec_dist_mm
        self.prec_dist_ppm = prec_dist_ppm
        self.inter_conf = inter_conf

    def calculate(self) -> LeastSquaresResult:
        n_obs = len(self.targets)

        target_to_col = {}
        for t in self.targets:
            if t.target_name not in target_to_col:
                target_to_col[t.target_name] = len(target_to_col)

        n_unk = len(target_to_col)

        n_eq = 2 * n_obs
        a = np.zeros((n_eq, 2 * n_unk))
        l = np.zeros(n_eq)
        sigma_dir = np.zeros(n_obs)
        sigma_dist = np.zeros(n_obs)

        for i, t in enumerate(self.targets):
            col = target_to_col[t.target_name]
            idx_dx = 2 * col
            idx_dy = 2 * col + 1

            if t.dist_utm <= 0:
                raise ValueError(
                    f"Distancia UTM no positiva para {t.target_name}: {t.dist_utm}"
                )

            de = t.approx_x - self.station_x
            dn = t.approx_y - self.station_y
            dist_calc = math.hypot(de, dn)
            if dist_calc <= 0:
                raise ValueError(
                    f"Distancia calculada nula para {t.target_name}: el punto está "
                    f"co-localizado con la estación."
                )

            acim_calc = math.atan2(de, dn) / self.gon_r
            if acim_calc < 0.0:
                acim_calc += 400.0

            # --- Matriz A ---
            # Fila dirección
            dir_row = i
            a[dir_row, idx_dx] = dn * self.r_cc / (dist_calc * dist_calc)
            a[dir_row, idx_dy] = -de * self.r_cc / (dist_calc * dist_calc)

            # Fila distancia
            dist_row = n_obs + i
            a[dist_row, idx_dx] = de / t.dist_utm
            a[dist_row, idx_dy] = dn / t.dist_utm

            # --- Matriz L ---
            # Dirección (cc)
            l[dir_row] = -(acim_calc - t.acimut_observado) * 10000.0
            # Distancia (m)
            l[dist_row] = -(dist_calc - t.dist_utm)

            # --- Precisiones a priori ---
            sigma_dir[i] = math.sqrt(
                (self.prec_ang_etr * self.s_sexa_cc) ** 2
                + (t.prec_senal / t.dist_utm * self.r_cc) ** 2
                + t.prec_punteria_cc ** 2
            )
            sigma_dist[i] = math.sqrt(
                t.prec_senal ** 2
                + (self.prec_dist_mm / 1000.0 + self.prec_dist_ppm * 1e-6 * t.dist_utm) ** 2
            )

        # --- Matriz P (diagonal) ---
        p_diag = np.zeros(n_eq)
        p_diag[:n_obs] = 1.0 / (sigma_dir ** 2)
        p_diag[n_obs:] = 1.0 / (sigma_dist ** 2)
        p = np.diag(p_diag)

        # --- Cadena MMC ---
        tra_a = a.T
        tra_a_p = tra_a @ p
        n_mat = tra_a_p @ a

        try:
            inver_n = np.linalg.inv(n_mat)
        except np.linalg.LinAlgError:
            raise ValueError(
                "La matriz N (AᵀPA) es singular: no se puede invertir. "
                "Verifique que haya al menos un punto visado con distancias no nulas."
            )

        t_vec = tra_a_p @ l
        x_vec = inver_n @ t_vec
        v_vec = a @ x_vec - l
        tra_v_p = v_vec.T @ p

        vtpv = float(tra_v_p @ v_vec)
        num_equations = n_eq
        num_unknowns = 2 * n_unk
        redundancy = num_equations - num_unknowns

        warnings: list[str] = []
        var_post: float = 0.0
        desv_post: float = 0.0
        prec: np.ndarray = np.zeros(2 * n_unk)

        if redundancy > 0:
            var_post = vtpv / redundancy
            desv_post = math.sqrt(var_post)
            prec = desv_post * self.inter_conf * np.sqrt(np.diag(inver_n))
        else:
            warnings.append(
                f"Redundancia = {redundancy} (<= 0): sistema compatible determinado. "
                "σ̂², desviación estándar a posteriori y precisiones no definidas (se "
                "fijan a 0). Las coordenadas ajustadas son válidas."
            )

        # --- Coordenadas ajustadas ---
        target_names = [""] * n_unk
        for name, col in target_to_col.items():
            target_names[col] = name

        adjusted_coords: list[tuple[str, float, float]] = []
        for col in range(n_unk):
            name = target_names[col]
            dx = float(x_vec[2 * col])
            dy = float(x_vec[2 * col + 1])
            # approx_x / approx_y del primer target con ese nombre
            approx_x = next(t.approx_x for t in self.targets if t.target_name == name)
            approx_y = next(t.approx_y for t in self.targets if t.target_name == name)
            adjusted_coords.append((name, approx_x + dx, approx_y + dy))

        logger.debug(
            "MMC: %d ecuaciones, %d incógnitas, redundancia=%d, desv_post=%s",
            num_equations, num_unknowns, redundancy, f"{desv_post:.6f}" if redundancy > 0 else "N/D",
        )

        return LeastSquaresResult(
            sigma_dir=sigma_dir,
            sigma_dist=sigma_dist,
            a=a,
            tra_a=tra_a,
            p=p,
            tra_a_p=tra_a_p,
            l=l,
            n=n_mat,
            inver_n=inver_n,
            t=t_vec,
            x=x_vec,
            v=v_vec,
            tra_v_p=tra_v_p,
            num_equations=num_equations,
            num_unknowns=num_unknowns,
            redundancy=redundancy,
            var_post=var_post,
            desv_post=desv_post,
            inter_conf=self.inter_conf,
            prec=prec,
            adjusted_coords=adjusted_coords,
            warnings=warnings,
        )
