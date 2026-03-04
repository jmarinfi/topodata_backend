from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.base import Base


class Coordinate(Base):
    __tablename__ = "coordinates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_name: Mapped[str] = mapped_column(String(255))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)

    type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {"polymorphic_on": "type", "polymorphic_identity": "coordinate"}
