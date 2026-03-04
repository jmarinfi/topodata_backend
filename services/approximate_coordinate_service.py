from api.schemas import (
    ApproximateCoordinateCreate,
    ApproximateCoordinateResponse,
    ApproximateCoordinateUpdate,
)
from data.repositories import (
    ApproximateCoordinateRepository,
    BesselObservationRepository,
)


class ApproximateCoordinateService:
    """Servicio para la gestión de coordenadas aproximadas."""

    def __init__(
        self,
        repository: ApproximateCoordinateRepository,
        repository_bessel_observation: BesselObservationRepository,
    ) -> None:
        self.repository = repository
        self.repository_bessel_observation = repository_bessel_observation

    def get_approximate_coordinates(self) -> list[ApproximateCoordinateResponse]:
        approximate_coordinates = self.repository.get_all()
        return [
            ApproximateCoordinateResponse.model_validate(approximate_coordinate)
            for approximate_coordinate in approximate_coordinates
        ]

    def get_approximate_coordinate_by_bessel_observation(
        self, bessel_observation_id: int
    ) -> ApproximateCoordinateResponse:
        approximate_coordinate = self.repository.get_by_bessel_observation(
            bessel_observation_id
        )
        if not approximate_coordinate:
            raise ValueError(
                f"La observación de Bessel con id {bessel_observation_id} no tiene ninguna coordenada aproximada asociada."
            )
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def get_approximate_coordinate(
        self, approximate_coordinate_id: int
    ) -> ApproximateCoordinateResponse:
        approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id {approximate_coordinate_id} no encontrada."
            )
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def get_number_approximate_coordinates(self) -> int:
        return self.repository.count()

    def create_approximate_coordinate(
        self, approximate_coordinate_data: ApproximateCoordinateCreate
    ) -> ApproximateCoordinateResponse:
        bessel_observation = self.repository_bessel_observation.get(
            approximate_coordinate_data.bessel_observation_id
        )
        if not bessel_observation:
            raise ValueError(
                f"Observación de Bessel con id {approximate_coordinate_data.bessel_observation_id} no encontrada."
            )

        attributes = approximate_coordinate_data.model_dump()
        approximate_coordinate = self.repository.create(attributes)
        self.repository.refresh(approximate_coordinate)
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def update_approximate_coordinate(
        self,
        approximate_coordinate_id: int,
        approximate_coordinate_data: ApproximateCoordinateUpdate,
    ) -> ApproximateCoordinateResponse:
        db_approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not db_approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id {approximate_coordinate_id} no encontrada."
            )

        attributes = approximate_coordinate_data.model_dump()
        approximate_coordinate = self.repository.update(
            db_approximate_coordinate, attributes
        )
        self.repository.refresh(approximate_coordinate)
        return ApproximateCoordinateResponse.model_validate(approximate_coordinate)

    def delete_approximate_coordinate(self, approximate_coordinate_id: int) -> None:
        db_approximate_coordinate = self.repository.get(approximate_coordinate_id)
        if not db_approximate_coordinate:
            raise ValueError(
                f"Coordenada aproximada con id: {approximate_coordinate_id} no encontrada."
            )
        self.repository.delete(db_approximate_coordinate)
