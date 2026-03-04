from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.coordinate import Coordinate


class ApproximateCoordinate(Coordinate):
    __tablename__ = "approximate_coordinates"

    id: Mapped[int] = mapped_column(ForeignKey("coordinates.id"), primary_key=True)
    bessel_observation_id: Mapped[int] = mapped_column(
        ForeignKey("bessel_observations.id"), index=True
    )

    __mapper_args__ = {"polymorphic_identity": "approximate"}
