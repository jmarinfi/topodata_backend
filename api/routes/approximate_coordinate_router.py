from fastapi import APIRouter, HTTPException

from api.dependencies import ApproximateCoordinateServiceDep
from api.schemas import (
    ApproximateCoordinateCreate,
    ApproximateCoordinateResponse,
    ApproximateCoordinateUpdate,
)

router = APIRouter(
    prefix="/api/v1/approximate-coordinates", tags=["approximate-coordinates"]
)


@router.get(
    "/",
    response_model=list[ApproximateCoordinateResponse],
)
def get_approximate_coordinates(service: ApproximateCoordinateServiceDep):
    return service.get_approximate_coordinates()


@router.get(
    "/by-bessel-observation/{bessel_observation_id}",
    response_model=ApproximateCoordinateResponse,
)
def get_approximate_coordinate_by_bessel_observation(
    bessel_observation_id: int, service: ApproximateCoordinateServiceDep
):
    return service.get_approximate_coordinate_by_bessel_observation(
        bessel_observation_id
    )


@router.get("/count", response_model=int)
def get_number_approximate_coordinates(service: ApproximateCoordinateServiceDep):
    return service.get_number_approximate_coordinates()


@router.get(
    "/{approximate_coordinate_id}", response_model=ApproximateCoordinateResponse
)
def get_approximate_coordinate(
    approximate_coordinate_id: int, service: ApproximateCoordinateServiceDep
):
    try:
        return service.get_approximate_coordinate(approximate_coordinate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ApproximateCoordinateResponse, status_code=201)
def create_approximate_coordinate(
    approximate_coordinate_in: ApproximateCoordinateCreate,
    service: ApproximateCoordinateServiceDep,
):
    try:
        return service.create_approximate_coordinate(approximate_coordinate_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{approximate_coordinate_id}", response_model=ApproximateCoordinateResponse
)
def update_approximate_coordinate(
    approximate_coordinate_id: int,
    approximate_coordinate_in: ApproximateCoordinateUpdate,
    service: ApproximateCoordinateServiceDep,
):
    try:
        return service.update_approximate_coordinate(
            approximate_coordinate_id, approximate_coordinate_in
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{approximate_coordinate_id}", status_code=204)
def delete_approximate_coordinate(
    approximate_coordinate_id: int, service: ApproximateCoordinateServiceDep
):
    try:
        service.delete_approximate_coordinate(approximate_coordinate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
