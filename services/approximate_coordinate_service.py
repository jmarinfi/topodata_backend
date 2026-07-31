import logging
from dataclasses import dataclass, field

from api.schemas import (
    AdjustedCoordinateCreate,
    AdjustedCoordinateResponse,
    ApproximateCoordinateCreate,
    ApproximateCoordinateResponse,
    ApproximateCoordinateUpdate,
    BesselObservationResponse,
    RawObservationResponse,
    ReferenceCoordinateResponse,
    StationSetupResponse,
)
from data.database.models import Project as ProjectModel
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
from services.calculations.approximate_coordinate_calculator import (
    ApproximateCoordinateCalculator,
    RadiacionResult,
)
from services.calculations.least_squares_adjuster import (
    LeastSquaresAdjuster,
    LeastSquaresResult,
    LsTarget,
)
from services.calculations.matrix_io import scalar_to_bytes, to_bytes
from services.calculations.station_position_calculator import StationPositionCalculator

logger = logging.getLogger(__name__)


@dataclass
class ApproximateCoordinateCalculationResult:
    """Resultado del cálculo de coordenadas aproximadas para un estacionamiento.

    ``warnings`` se rellena cuando hay problemas no bloqueantes (p.ej. pocas
    referencias observadas, pero suficientes para el cálculo).
    """

    approximate_coordinates: list[ApproximateCoordinateResponse]
    etr_x: float
    etr_y: float
    etr_z: float
    k_utm: float
    desorientacion: float
    warnings: list[str]
    adjusted_coordinates: list[AdjustedCoordinateResponse] = field(
        default_factory=list
    )
    desv_post: float | None = None
    num_equations: int | None = None
    num_unknowns: int | None = None
    redundancy: int | None = None


class ApproximateCoordinateService:
    """Servicio para la gestión de coordenadas aproximadas."""

    def __init__(
        self,
        repository: ApproximateCoordinateRepository,
        repository_bessel_observation: BesselObservationRepository,
        repository_station_setup: StationSetupRepository,
        repository_project: ProjectRepository,
        repository_reference_coordinate: ReferenceCoordinateRepository,
        repository_raw_observation: RawObservationRepository,
        repository_import_session: ImportSessionRepository,
        repository_adjusted_coordinate: AdjustedCoordinateRepository,
    ) -> None:
        self.repository = repository
        self.repository_bessel_observation = repository_bessel_observation
        self.repository_station_setup = repository_station_setup
        self.repository_project = repository_project
        self.repository_reference_coordinate = repository_reference_coordinate
        self.repository_raw_observation = repository_raw_observation
        self.repository_import_session = repository_import_session
        self.repository_adjusted_coordinate = repository_adjusted_coordinate

    def get_approximate_coordinates(self) -> list[ApproximateCoordinateResponse]:
        approximate_coordinates = self.repository.get_all()
        return [
            ApproximateCoordinateResponse.model_validate(approximate_coordinate)
            for approximate_coordinate in approximate_coordinates
        ]

    def get_approximate_coordinates_by_station_setup(
        self, station_setup_id: int
    ) -> list[ApproximateCoordinateResponse]:
        """Coordenadas aproximadas de todas las observaciones Bessel de un
        estacionamiento."""
        coords = self.repository.get_by_station_setup(station_setup_id)
        return [ApproximateCoordinateResponse.model_validate(c) for c in coords]

    def get_approximate_coordinate_by_bessel_observation(
        self, bessel_observation_id: int
    ) -> ApproximateCoordinateResponse:
        approximate_coordinate = self.repository.get_by_bessel_observation(
            bessel_observation_id
        )
        if not approximate_coordinate:
            raise ValueError(
                f"La observación de Bessel con id {bessel_observation_id} no tiene ninguna coordenada aproximada asociada."
            )
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def get_approximate_coordinate(
        self, approximate_coordinate_id: int
    ) -> ApproximateCoordinateResponse:
        approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id {approximate_coordinate_id} no encontrada."
            )
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def get_number_approximate_coordinates(self) -> int:
        return self.repository.count()

    def create_approximate_coordinate(
        self, approximate_coordinate_data: ApproximateCoordinateCreate
    ) -> ApproximateCoordinateResponse:
        bessel_observation = self.repository_bessel_observation.get(
            approximate_coordinate_data.bessel_observation_id
        )
        if not bessel_observation:
            raise ValueError(
                f"Observación de Bessel con id {approximate_coordinate_data.bessel_observation_id} no encontrada."
            )

        attributes = approximate_coordinate_data.model_dump()
        approximate_coordinate = self.repository.create(attributes)
        self.repository.refresh(approximate_coordinate)
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def update_approximate_coordinate(
        self,
        approximate_coordinate_id: int,
        approximate_coordinate_data: ApproximateCoordinateUpdate,
    ) -> ApproximateCoordinateResponse:
        db_approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not db_approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id {approximate_coordinate_id} no encontrada."
            )

        attributes = approximate_coordinate_data.model_dump()
        approximate_coordinate = self.repository.update(
            db_approximate_coordinate, attributes
        )
        self.repository.refresh(approximate_coordinate)
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def delete_approximate_coordinate(self, approximate_coordinate_id: int) -> None:
        db_approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not db_approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id: {approximate_coordinate_id} no encontrada."
            )
        self.repository.delete(db_approximate_coordinate)

    # ------------------------------------------------------------------ #
    # Pipeline completo de coordenadas aproximadas (B2.7)
    # ------------------------------------------------------------------ #

    def calculate_for_station_setup(
        self, station_setup_id: int
    ) -> ApproximateCoordinateCalculationResult:
        """Ejecuta el pipeline completo de coordenadas aproximadas.

        Carga todos los datos necesarios (estacionamiento, proyecto,
        referencias, observaciones Bessel y brutas), ejecuta las 5 etapas
        del pipeline (Cassini → k_utm → Z → desorientación → radiación),
        persiste los resultados en el estacionamiento y las coordenadas
        aproximadas, y devuelve el resultado.

        Es **idempotente**: las coordenadas aproximadas previas del
        estacionamiento se borran y se reescriben.

        Raises:
            ValueError: Si el estacionamiento no existe, si el proyecto no
                tiene configurada la zona UTM o los parámetros del elipsoide,
                o si no hay suficientes referencias observadas (≥3).
        """
        warnings: list[str] = []

        # 1. Cargar entidades necesarias.
        station_setup = self.repository_station_setup.get(station_setup_id)
        if not station_setup:
            raise ValueError(
                f"Estacionamiento con id {station_setup_id} no encontrado."
            )

        import_session = self.repository_import_session.get(
            station_setup.import_session_id
        )
        if not import_session:
            raise ValueError(
                f"Sesión de importación con id {station_setup.import_session_id} "
                f"no encontrada."
            )

        project: ProjectModel | None = self.repository_project.get(
            import_session.project_id
        )
        if not project:
            raise ValueError(
                f"Proyecto con id {import_session.project_id} no encontrado."
            )

        if not project.zona_utm:
            raise ValueError(
                f"El proyecto '{project.name}' no tiene configurada la zona UTM."
            )

        # Constantes de clase + columnas del proyecto.
        gon_r = ProjectModel.GON_R
        earth_radius = ProjectModel.EARTH_RADIUS
        r_cc = ProjectModel.R_CC
        s_sexa_cc = ProjectModel.S_SEXA_CC
        k_0_adim = ProjectModel.K_0_ADIM
        kt_coef_refr = import_session.kt_coef_refr
        prec_ang_etr = import_session.prec_ang_etr
        prec_dist_mm = import_session.prec_dist_mm
        prec_dist_ppm = import_session.prec_dist_ppm

        # 2. Cargar observaciones y referencias.
        bessel_obs = self.repository_bessel_observation.get_by_station_setup(
            station_setup_id
        )
        if not bessel_obs:
            raise ValueError(
                f"El estacionamiento {station_setup_id} no tiene observaciones "
                f"Bessel. Importe primero un archivo GKA."
            )

        raw_obs = self.repository_raw_observation.get_by_station_setup(station_setup_id)

        refs = self.repository_reference_coordinate.get_by_project(project.id)
        if len(refs) < 3:
            raise ValueError(
                f"El proyecto '{project.name}' necesita al menos 3 coordenadas "
                f"de referencia para calcular las coordenadas aproximadas "
                f"(tiene {len(refs)})."
            )

        # Convertir a schemas de respuesta para los calculadores.
        bessel_responses = [
            BesselObservationResponse.model_validate(o) for o in bessel_obs
        ]
        raw_responses = (
            [RawObservationResponse.model_validate(o) for o in raw_obs]
            if raw_obs
            else []
        )
        ref_responses = [ReferenceCoordinateResponse.model_validate(r) for r in refs]

        # 3. Etapa 1: inversa planimétrica de Cassini → etr_x, etr_y.
        try:
            resection = StationPositionCalculator(
                references=ref_responses,
                bessel_observations=bessel_responses,
                gon_r=gon_r,
            ).calculate_resection()
        except ValueError as e:
            raise ValueError(
                f"No se pudo calcular la posición de la estación por inversa "
                f"planimétrica: {e}"
            ) from e

        etr_x, etr_y = resection.etr_x, resection.etr_y

        if resection.combinations < len(ref_responses):
            warnings.append(
                f"Solo {resection.combinations} de "
                f"{len(ref_responses)} referencias contribuyeron a la inversa "
                f"planimétrica."
            )

        # 4. Etapa 2: factor de escala UTM.
        k_utm = StationPositionCalculator.calculate_k_utm(
            etr_x=etr_x,
            etr_y=etr_y,
            zona_utm=project.zona_utm,
            a_elip=project.a_elip,
            b_elip=project.b_elip,
            f_elip=project.f_elip,
            k_0_adim=k_0_adim,
        )

        # 5. Etapa 3: cota de la estación (ZEST).
        try:
            z_result = StationPositionCalculator.calculate_z_est(
                etr_x=etr_x,
                etr_y=etr_y,
                k_utm=k_utm,
                references=ref_responses,
                bessel_observations=bessel_responses,
                raw_observations=raw_responses,
                station_height=station_setup.station_height,
                gon_r=gon_r,
                earth_radius=earth_radius,
                s_sexa_cc=s_sexa_cc,
                kt_coef_refr=kt_coef_refr,
                prec_ang_etr=prec_ang_etr,
            )
        except ValueError as e:
            raise ValueError(f"No se pudo calcular la cota de la estación: {e}") from e

        etr_z = z_result.z_est

        # 6. Etapa 4: desorientación.
        try:
            desorientacion_result = (
                ApproximateCoordinateCalculator.calculate_desorientacion(
                    etr_x=etr_x,
                    etr_y=etr_y,
                    references=ref_responses,
                    bessel_observations=bessel_responses,
                    gon_r=gon_r,
                )
            )
        except ValueError as e:
            raise ValueError(
                f"No se pudo calcular la desorientación del estacionamiento: {e}"
            ) from e

        desorientacion = desorientacion_result.desorientacion

        # 7. Etapa 5: radiación → coordenadas aproximadas.
        radiaciones: list[RadiacionResult] = (
            ApproximateCoordinateCalculator.calculate_all_radiaciones(
                bessel_observations=bessel_responses,
                etr_x=etr_x,
                etr_y=etr_y,
                etr_z=etr_z,
                k_utm=k_utm,
                desorientacion=desorientacion,
                gon_r=gon_r,
                earth_radius=earth_radius,
                r_cc=r_cc,
                kt_coef_refr=kt_coef_refr,
            )
        )

        # 8. Capturar precisiones de registros previos (antes del borrado idempotente).
        prev_approx = self.repository.get_by_station_setup(station_setup_id)
        prec_by_target: dict[str, tuple[float, float]] = {}
        for c in prev_approx:
            prec_by_target[c.target_name] = (c.prec_senal, c.prec_punteria_cc)

        # 9. MMC: ajuste por mínimos cuadrados (solo puntos de control).
        ref_names = {r.target_name for r in ref_responses}
        control_radiaciones = [
            r for r in radiaciones if r.target_name not in ref_names
        ]

        ls_result: LeastSquaresResult | None = None
        if control_radiaciones:
            ls_targets: list[LsTarget] = []
            for r in control_radiaciones:
                ps, pp = prec_by_target.get(r.target_name, (0.0, 3.09))
                ls_targets.append(
                    LsTarget(
                        target_name=r.target_name,
                        approx_x=r.x,
                        approx_y=r.y,
                        dist_utm=r.dist_utm,
                        acimut_observado=r.acimut,
                        prec_senal=ps,
                        prec_punteria_cc=pp,
                    )
                )
            try:
                adjuster = LeastSquaresAdjuster(
                    station_x=etr_x,
                    station_y=etr_y,
                    targets=ls_targets,
                    gon_r=gon_r,
                    r_cc=r_cc,
                    s_sexa_cc=s_sexa_cc,
                    prec_ang_etr=prec_ang_etr,
                    prec_dist_mm=prec_dist_mm,
                    prec_dist_ppm=prec_dist_ppm,
                )
                ls_result = adjuster.calculate()
            except ValueError as e:
                warnings.append(f"MMC falló: {e}")
        else:
            warnings.append(
                "MMC omitido: no hay puntos de control (todos los visados son "
                "referencias)."
            )

        # 10. Persistir etr_*, k_utm, desorientacion y matrices en el estacionamiento.
        update_data = {
            "etr_x": etr_x,
            "etr_y": etr_y,
            "etr_z": etr_z,
            "k_utm": k_utm,
            "desorientacion": desorientacion,
        }
        if ls_result is not None:
            update_data.update(
                {
                    "v_matrix": to_bytes(ls_result.v),
                    "a_matrix": to_bytes(ls_result.a),
                    "tra_a_matrix": to_bytes(ls_result.tra_a),
                    "p_matrix": to_bytes(ls_result.p),
                    "tra_a_p_matrix": to_bytes(ls_result.tra_a_p),
                    "x_matrix": to_bytes(ls_result.x),
                    "l_matrix": to_bytes(ls_result.l),
                    "n_matrix": to_bytes(ls_result.n),
                    "inver_n_matrix": to_bytes(ls_result.inver_n),
                    "t_matrix": to_bytes(ls_result.t),
                    "tra_v_p_matrix": to_bytes(ls_result.tra_v_p),
                    "prec_matrix": to_bytes(ls_result.prec),
                    "adjust_coord_matrix": to_bytes(
                        [(n, x, y) for n, x, y in ls_result.adjusted_coords]
                    ),
                    "desv_post_matrix": scalar_to_bytes(ls_result.desv_post),
                    "var_post_matrix": scalar_to_bytes(ls_result.var_post),
                    "num_equations_matrix": scalar_to_bytes(ls_result.num_equations),
                    "num_unknowns_matrix": scalar_to_bytes(ls_result.num_unknowns),
                    "inter_conf_matrix": scalar_to_bytes(ls_result.inter_conf),
                }
            )
            warnings.extend(ls_result.warnings)

        self.repository_station_setup.update(station_setup, update_data)

        # 11. Idempotencia ampliada: borrar coords aproximadas y ajustadas previas.
        self.repository.delete_by_station_setup(station_setup_id)
        self.repository_adjusted_coordinate.delete_by_station_setup(
            station_setup_id
        )

        # 12. Recrear coordenadas aproximadas (preservando prec_senal/prec_punteria).
        persisted: list[ApproximateCoordinateResponse] = []
        for r in radiaciones:
            bessel_id: int | None = None
            for bo in bessel_responses:
                if bo.target_name == r.target_name:
                    bessel_id = bo.id
                    break

            if bessel_id is None:
                warnings.append(
                    f"No se encontró el id de la observación Bessel para "
                    f"'{r.target_name}'; se omite su coordenada aproximada."
                )
                continue

            ps, pp = prec_by_target.get(r.target_name, (0.0, 3.09))
            create_data = ApproximateCoordinateCreate(
                target_name=r.target_name,
                x=r.x,
                y=r.y,
                z=r.z,
                bessel_observation_id=bessel_id,
                prec_senal=ps,
                prec_punteria_cc=pp,
            )
            coord = self.repository.create(create_data.model_dump())
            self.repository.refresh(coord)
            persisted.append(ApproximateCoordinateResponse.model_validate(coord))

        # 13. Crear coordenadas ajustadas (si el MMC fue OK).
        adjusted_responses: list[AdjustedCoordinateResponse] = []
        if ls_result is not None:
            for k, (name, x_adj, y_adj) in enumerate(
                ls_result.adjusted_coords
            ):
                bessel_id = None
                for bo in bessel_responses:
                    if bo.target_name == name:
                        bessel_id = bo.id
                        break

                if bessel_id is None:
                    warnings.append(
                        f"No se encontró Bessel observation para punto "
                        f"ajustado '{name}'; se omite."
                    )
                    continue

                z_val = 0.0
                for r in control_radiaciones:
                    if r.target_name == name:
                        z_val = r.z
                        break

                adj_create = AdjustedCoordinateCreate(
                    target_name=name,
                    x=x_adj,
                    y=y_adj,
                    z=z_val,
                    bessel_observation_id=bessel_id,
                    prec_x=float(ls_result.prec[2 * k]),
                    prec_y=float(ls_result.prec[2 * k + 1]),
                )
                coord = self.repository_adjusted_coordinate.create(
                    adj_create.model_dump()
                )
                self.repository_adjusted_coordinate.refresh(coord)
                adjusted_responses.append(
                    AdjustedCoordinateResponse.model_validate(coord)
                )

        return ApproximateCoordinateCalculationResult(
            approximate_coordinates=persisted,
            etr_x=etr_x,
            etr_y=etr_y,
            etr_z=etr_z,
            k_utm=k_utm,
            desorientacion=desorientacion,
            warnings=warnings,
            adjusted_coordinates=adjusted_responses,
            desv_post=ls_result.desv_post if ls_result else None,
            num_equations=ls_result.num_equations if ls_result else None,
            num_unknowns=ls_result.num_unknowns if ls_result else None,
            redundancy=ls_result.redundancy if ls_result else None,
        )
