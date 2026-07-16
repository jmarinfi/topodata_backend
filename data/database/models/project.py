import math
from typing import ClassVar, Optional

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    coordinate_system: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    locale_string: Mapped[Optional[str]] = mapped_column(String(50), default="es-ES")
    zona_utm: Mapped[Optional[str]] = mapped_column(String(3))

    # Variables para los cálculos
    a_elip: Mapped[float] = mapped_column(Float)
    b_elip: Mapped[float] = mapped_column(Float)
    f_elip: Mapped[float] = mapped_column(Float)
    inv_f_elip: Mapped[float] = mapped_column(Float)
    # Constantes para los cálculos
    GON_R: ClassVar[float] = math.pi / 200.0
    EARTH_RADIUS: ClassVar[float] = 6378000.0
    S_SEXA_CC: ClassVar[float] = 250.0 / 81.0
    R_CC: ClassVar[float] = 2000000.0 / math.pi
    K_0_ADIM: ClassVar[float] = 0.9996  # Factor de escala UTM del meridiano central
