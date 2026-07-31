from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.coordinate import Coordinate


class AdjustedCoordinate(Coordinate):
    __tablename__ = "adjusted_coordinates"

    id: Mapped[int] = mapped_column(ForeignKey("coordinates.id"), primary_key=True)
    bessel_observation_id: Mapped[int] = mapped_column(
        ForeignKey("bessel_observations.id"), index=True
    )
    prec_x: Mapped[float] = mapped_column(Float)
    prec_y: Mapped[float] = mapped_column(Float)

    __mapper_args__ = {"polymorphic_identity": "adjusted"}
