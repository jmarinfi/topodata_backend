from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models import Base


class BesselObservation(Base):
    __tablename__ = "bessel_observations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_setup_id: Mapped[int] = mapped_column(
        ForeignKey("station_setups.id"), index=True
    )
    target_name: Mapped[str] = mapped_column(String(255))
    hz_angle_direct: Mapped[float] = mapped_column(Float)
    v_angle_direct: Mapped[float] = mapped_column(Float)
    distance_direct: Mapped[float] = mapped_column(Float)
    hz_angle_inverse: Mapped[float] = mapped_column(Float)
    v_angle_inverse: Mapped[float] = mapped_column(Float)
    distance_inverse: Mapped[float] = mapped_column(Float)
    hz_angle_bessel: Mapped[float] = mapped_column(Float)
    v_angle_bessel: Mapped[float] = mapped_column(Float)
    distance_bessel: Mapped[float] = mapped_column(Float)
    hz_angle_delta: Mapped[float] = mapped_column(Float)
    v_angle_delta: Mapped[float] = mapped_column(Float)
    distance_delta: Mapped[float] = mapped_column(Float)
