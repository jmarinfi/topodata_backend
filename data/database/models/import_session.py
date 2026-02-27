from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    filename: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    raw_file_content: Mapped[str] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    # Variables para los cálculos
    kt_coef_refr: Mapped[float] = mapped_column(Float, default=0.13)
    prec_ang_etr: Mapped[float] = mapped_column(Float, default=0.5)
