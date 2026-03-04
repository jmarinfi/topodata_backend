from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.database.models.coordinate import Coordinate


class ReferenceCoordinate(Coordinate):
    __tablename__ = "reference_coordinates"

    id: Mapped[int] = mapped_column(ForeignKey("coordinates.id"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    __mapper_args__ = {"polymorphic_identity": "reference"}
