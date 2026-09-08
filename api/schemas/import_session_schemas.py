from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportSessionBase(BaseModel):
    """Esquema base para las sesiones de importación."""

    project_id: int = Field(..., description="Id del proyecto")
    filename: str = Field(
        ..., min_length=1, max_length=1024, description="Nombre del fichero"
    )
    content_hash: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Resumen hash del contenido del fichero",
    )
    raw_file_content: str = Field(..., description="Contenido del fichero")
    kt_coef_refr: float = Field(
        default=0.13, gt=0, description="Coeficiente de refracción"
    )
    prec_ang_etr: float = Field(default=0.5, gt=0, description="Precisión angular")
    prec_dist_mm: float = Field(
        default=0.8, gt=0, description="Precisión del distanciómetro (mm)"
    )
    prec_dist_ppm: float = Field(
        default=1, gt=0, description="Precisión del distanciómetro (ppm)"
    )


class ImportSessionCreate(ImportSessionBase):
    """Esquema para crear sesiones de importación."""

    ...


class ImportSessionUpdate(ImportSessionBase):
    """Esquema para actualizar sesiones de importación (PUT completo)."""

    ...


class ImportSessionResponse(ImportSessionBase):
    """Esquema para obtener sesiones de importación de la base de datos."""

    id: int
    imported_at: datetime = Field(..., description="Fecha de importación del fichero")
    kt_coef_refr: float = Field(..., gt=0, description="Coeficiente de refracción")
    prec_ang_etr: float = Field(..., gt=0, description="Precisión angular")

    model_config = ConfigDict(from_attributes=True)
