from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, LargeBinary, String, Text
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

    # Variables cálculos intermedios
    j_edm: Mapped[float | None] = mapped_column(Float, nullable=True)
    n_edm: Mapped[float | None] = mapped_column(Float, nullable=True)
    etr_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    etr_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    etr_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_utm: Mapped[float | None] = mapped_column(Float, nullable=True)
    desorientacion: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Orden de los puntos de control usados en el MMC
    ls_obs_targets: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Matrices
    v_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    a_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    tra_a_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    p_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    tra_a_p_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    x_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    l_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    n_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    inver_n_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    t_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    tra_v_p_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    desv_post_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    var_post_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    num_equations_matrix: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    num_unknowns_matrix: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    inter_conf_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    prec_matrix: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    adjust_coord_matrix: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
