from fastapi import APIRouter, HTTPException

from api.dependencies import AdjustedCoordinateServiceDep, CurrentUser
from api.schemas import AdjustedCoordinateResponse

router = APIRouter(
    prefix="/api/v1/adjusted-coordinates", tags=["adjusted-coordinates"]
)


@router.get("/", response_model=list[AdjustedCoordinateResponse])
def get_adjusted_coordinates(
    service: AdjustedCoordinateServiceDep,
    _: CurrentUser,
):
    return service.get_all()


@router.get(
    "/by-station-setup/{station_setup_id}",
    response_model=list[AdjustedCoordinateResponse],
)
def get_adjusted_coordinates_by_station_setup(
    station_setup_id: int,
    service: AdjustedCoordinateServiceDep,
    _: CurrentUser,
):
    return service.get_by_station_setup(station_setup_id)


@router.get("/count", response_model=int)
def get_number_adjusted_coordinates(
    service: AdjustedCoordinateServiceDep,
    _: CurrentUser,
):
    return service.count()


@router.get("/{adjusted_coordinate_id}", response_model=AdjustedCoordinateResponse)
def get_adjusted_coordinate(
    adjusted_coordinate_id: int,
    service: AdjustedCoordinateServiceDep,
    _: CurrentUser,
):
    try:
        return service.get(adjusted_coordinate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
