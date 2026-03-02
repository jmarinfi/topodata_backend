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


class ImportSessionCreate(ImportSessionBase):
    """Esquema para crear sesiones de importación."""

    ...


class ImportSessionUpdate(ImportSessionBase):
    """Esquema para actualizar sesiones de importación (PUT completo)."""

    kt_coef_refr: float = Field(..., gt=0, description="Coeficiente de refracción")
    prec_ang_etr: float = Field(..., gt=0, description="Precisión angular")


class ImportSessionResponse(ImportSessionBase):
    """Esquema para obtener sesiones de importación de la base de datos."""

    id: int
    imported_at: datetime = Field(..., description="Fecha de importación del fichero")
    kt_coef_refr: float = Field(..., gt=0, description="Coeficiente de refracción")
    prec_ang_etr: float = Field(..., gt=0, description="Precisión angular")

    model_config = ConfigDict(from_attributes=True)
