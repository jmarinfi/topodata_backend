from api.schemas import (
    ReferenceCoordinateCreate,
    ReferenceCoordinateResponse,
    ReferenceCoordinateUpdate,
)
from data.repositories import ProjectRepository, ReferenceCoordinateRepository


class ReferenceCoordinateService:
    """Servicio para la gestión de coordenadas de referencia."""

    def __init__(
        self,
        repository: ReferenceCoordinateRepository,
        repository_project: ProjectRepository,
    ) -> None:
        self.repository = repository
        self.repository_project = repository_project

    def get_reference_coordinates(self) -> list[ReferenceCoordinateResponse]:
        reference_coordinates = self.repository.get_all()
        return [
            ReferenceCoordinateResponse.model_validate(reference_coordinate)
            for reference_coordinate in reference_coordinates
        ]

    def get_reference_coordinates_by_project(
        self, project_id: int
    ) -> list[ReferenceCoordinateResponse]:
        reference_coordinates = self.repository.get_by_project(project_id)
        return [
            ReferenceCoordinateResponse.model_validate(reference_coordinate)
            for reference_coordinate in reference_coordinates
        ]

    def get_reference_coordinate(
        self, reference_coordinate_id: int
    ) -> ReferenceCoordinateResponse:
        reference_coordinate = self.repository.get(reference_coordinate_id)
        if not reference_coordinate:
            raise ValueError(
                f"Referencia con id {reference_coordinate_id} no encontrada."
            )
        return ReferenceCoordinateResponse.model_validate(reference_coordinate)

    def get_number_reference_coordinates(self) -> int:
        return self.repository.count()

    def create_reference_coordinate(
        self, reference_coordinate_data: ReferenceCoordinateCreate
    ) -> ReferenceCoordinateResponse:
        project = self.repository_project.get(reference_coordinate_data.project_id)
        if not project:
            raise ValueError(
                f"Proyecto con id {reference_coordinate_data.project_id} no encontrado."
            )

        attributes = reference_coordinate_data.model_dump()
        reference_coordinate = self.repository.create(attributes)
        self.repository.refresh(reference_coordinate)
        return ReferenceCoordinateResponse.model_validate(reference_coordinate)

    def update_reference_coordinate(
        self,
        reference_coordinate_id: int,
        reference_coordinate_data: ReferenceCoordinateUpdate,
    ) -> ReferenceCoordinateResponse:
        db_reference_coordinate = self.repository.get(reference_coordinate_id)
        if not db_reference_coordinate:
            raise ValueError(
                f"Referencia con id {reference_coordinate_id} no encontrada."
            )

        attributes = reference_coordinate_data.model_dump()
        reference_coordinate = self.repository.update(
            db_reference_coordinate, attributes
        )
        self.repository.refresh(reference_coordinate)
        return ReferenceCoordinateResponse.model_validate(reference_coordinate)

    def delete_reference_coordinate(self, reference_coordinate_id: int) -> None:
        db_reference_coordinate = self.repository.get(reference_coordinate_id)
        if not db_reference_coordinate:
            raise ValueError(
                f"Referencia con id {reference_coordinate_id} no encontrada."
            )
        self.repository.delete(db_reference_coordinate)
