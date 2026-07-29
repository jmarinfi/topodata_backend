from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"
    __table_args__ = (
        UniqueConstraint("project_id", "content_hash", name="uq_import_session_project_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    filename: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(512), index=True)
    raw_file_content: Mapped[str] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    kt_coef_refr: Mapped[float] = mapped_column(Float, default=0.13)
    prec_ang_etr: Mapped[float] = mapped_column(Float, default=0.5)
    prec_dist_mm: Mapped[float] = mapped_column(Float, default=0.8)
    prec_dist_ppm: Mapped[float] = mapped_column(Float, default=1)
