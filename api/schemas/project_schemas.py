from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pyproj import CRS


class ProjectBase(BaseModel):
    """Esquema base para proyectos de topografía."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre del proyecto"
    )
    coordinate_system: str = Field(
        ..., description="Sistema de coordenadas. Código EPSG."
    )
    description: str | None = Field(None, description="Descripción del proyecto")
    locale_string: str | None = Field(
        default="es-ES", max_length=50, description="Configuración regional"
    )
    zona_utm: str | None = Field(None, max_length=3, description="Zona UTM")

    # Parámetros técnicos derivados
    a_elip: float | None = Field(None, gt=0, description="Semi-eje mayor del elipsoide")
    b_elip: float | None = Field(None, gt=0, description="Semi-eje menor del elipsoide")
    f_elip: float | None = Field(None, description="Aplanamiento del elipsoide")
    inv_f_elip: float | None = Field(
        None, description="Inversa del aplanamiento del elipsoide"
    )
    # k_0: float | None = Field(None, gt=0, description="Factor de escala")

    @model_validator(mode="before")
    @classmethod
    def populate_geodetic_parametrs(cls, data: Any) -> Any:
        if isinstance(data, dict) and "coordinate_system" in data:
            try:
                # Crear el objeto CRS desde el string
                crs = CRS.from_user_input(data["coordinate_system"])
                ellipsoid = crs.ellipsoid

                if ellipsoid is not None:
                    # Extraer parámetros del elipsoide
                    a = ellipsoid.semi_major_metre
                    b = ellipsoid.semi_minor_metre
                    inv_f = ellipsoid.inverse_flattening
                    f = 1 / inv_f if inv_f != 0 else 0

                    # Factor de escala
                    k0 = 1.0
                    if crs.is_projected:
                        # Se busca en los parámetros de la conversión
                        conv_dict = crs.to_json_dict().get("conversion", {})
                        params = conv_dict.get("parameters", [])
                        for p in params:
                            # El nombre estándar EPSG para k0 es "Scale factor at natural origin"
                            if "Scale factor" in p.get("name", ""):
                                k0 = p.get("value")
                                break

                    data.update(
                        {
                            "a_elip": a,
                            "b_elip": b,
                            "f_elip": f,
                            "inv_f_elip": inv_f,
                            "k_0": k0,
                        }
                    )

            except Exception as e:
                raise ValueError(f"Sistema de coordenadas inválido o no soportado: {e}")

        return data


class ProjectCreate(ProjectBase):
    """Esquema para crear proyectos de topografía."""

    ...


class ProjectUpdate(ProjectBase):
    """Esquema para actualizar proyectos de topografía (PUT completo)."""

    ...


class ProjectResponse(ProjectBase):
    """Esquema para obtener proyectos de topografía de la base de datos."""

    id: int

    model_config = ConfigDict(from_attributes=True)
