from fastapi import APIRouter, HTTPException

from api.dependencies import CurrentUser, ReferenceCoordinateServiceDep
from api.schemas import (
    ReferenceCoordinateCreate,
    ReferenceCoordinateResponse,
    ReferenceCoordinateUpdate,
)

router = APIRouter(
    prefix="/api/v1/reference-coordinates", tags=["reference-coordinates"]
)


@router.get("/", response_model=list[ReferenceCoordinateResponse])
def get_reference_coordinates(
    service: ReferenceCoordinateServiceDep,
    _: CurrentUser,
    project_id: int | None = None,
):
    if project_id:
        return service.get_reference_coordinates_by_project(project_id)
    return service.get_reference_coordinates()


@router.get("/count", response_model=int)
def get_number_reference_coordinates(
    service: ReferenceCoordinateServiceDep,
    _: CurrentUser,
):
    return service.get_number_reference_coordinates()


@router.get("/{reference_coordinate_id}", response_model=ReferenceCoordinateResponse)
def get_reference_coordinate(
    reference_coordinate_id: int, service: ReferenceCoordinateServiceDep, _: CurrentUser
):
    try:
        return service.get_reference_coordinate(reference_coordinate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ReferenceCoordinateResponse, status_code=201)
def create_reference_coordinate(
    reference_coordinate_in: ReferenceCoordinateCreate,
    service: ReferenceCoordinateServiceDep,
    _: CurrentUser,
):
    try:
        return service.create_reference_coordinate(reference_coordinate_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{reference_coordinate_id}", response_model=ReferenceCoordinateResponse)
def update_reference_coordinate(
    reference_coordinate_id: int,
    reference_coordinate_in: ReferenceCoordinateUpdate,
    service: ReferenceCoordinateServiceDep,
    _: CurrentUser,
):
    try:
        return service.update_reference_coordinate(
            reference_coordinate_id, reference_coordinate_in
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{reference_coordinate_id}", status_code=204)
def delete_reference_coordinate(
    reference_coordinate_id: int, service: ReferenceCoordinateServiceDep, _: CurrentUser
):
    try:
        service.delete_reference_coordinate(reference_coordinate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
