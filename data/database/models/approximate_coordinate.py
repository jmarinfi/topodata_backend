from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.coordinate import Coordinate


class ApproximateCoordinate(Coordinate):
    __tablename__ = "approximate_coordinates"

    id: Mapped[int] = mapped_column(ForeignKey("coordinates.id"), primary_key=True)
    bessel_observation_id: Mapped[int] = mapped_column(
        ForeignKey("bessel_observations.id"), index=True
    )

    prec_senal: Mapped[float] = mapped_column(Float, default=0.0)
    prec_punteria_cc: Mapped[float] = mapped_column(Float, default=3.09)

    __mapper_args__ = {"polymorphic_identity": "approximate"}
