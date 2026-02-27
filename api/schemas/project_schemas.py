from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Esquema base para proyectos de topografía."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre del proyecto"
    )
    coordinate_system: str = Field(..., description="Sistema de coordenadas")
    description: str | None = Field(None, description="Descripción del proyecto")
    locale_string: str | None = Field(
        default="es-ES", max_length=50, description="Configuración regional"
    )
    zona_utm: str | None = Field(None, max_length=3, description="Zona UTM")
    a_elip: float = Field(..., gt=0, description="Semi-eje mayor del elipsoide")
    b_elip: float = Field(..., gt=0, description="Semi-eje menor del elipsoide")
    f_elip: float = Field(..., description="Aplanamiento del elipsoide")
    inv_f_elip: float = Field(..., description="Inversa del aplanamiento del elipsoide")
    k_0: float = Field(..., gt=0, description="Factor de escala")


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
