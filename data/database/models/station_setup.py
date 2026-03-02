from datetime import datetime

from sqlalchemy import String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models import Base


class StationSetup(Base):
    __tablename__ = "station_setups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_session_id: Mapped[int] = mapped_column(
        ForeignKey("import_sessions.id"), index=True
    )
    station_name: Mapped[str] = mapped_column(String(255))
    station_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    edm_refractive_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    edm_carrier_wavelength: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    etr_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    etr_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    etr_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_utm: Mapped[float | None] = mapped_column(Float, nullable=True)
    desorientacion: Mapped[float | None] = mapped_column(Float, nullable=True)
