from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models import Base


class RawObservation(Base):
    __tablename__ = "raw_observations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_setup_id: Mapped[int] = mapped_column(
        ForeignKey("station_setups.id"), index=True
    )
    target_name: Mapped[str] = mapped_column(String(255))
    target_number: Mapped[int]
    circle: Mapped[int]
    hz_angle: Mapped[float] = mapped_column(Float)
    v_angle: Mapped[float] = mapped_column(Float)
    distance_geom: Mapped[float] = mapped_column(Float)
    gis_prism_id: Mapped[int | None] = mapped_column(nullable=True)
    observation_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    prism_constant: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    refraction_coef: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev_hz: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev_dist: Mapped[float | None] = mapped_column(Float, nullable=True)
