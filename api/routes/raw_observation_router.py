from fastapi import APIRouter, HTTPException

from api.dependencies import CurrentUser, RawObservationServiceDep
from api.schemas import (
    RawObservationCreate,
    RawObservationResponse,
    RawObservationUpdate,
)

router = APIRouter(prefix="/api/v1/raw-observations", tags=["raw-observations"])


@router.get("/", response_model=list[RawObservationResponse])
def get_raw_observations(
    service: RawObservationServiceDep,
    _: CurrentUser,
    station_setup_id: int | None = None,
):
    if station_setup_id is not None:
        return service.get_raw_observations_by_station_setup(station_setup_id)
    return service.get_raw_observations()


@router.get("/count", response_model=int)
def get_number_raw_observations(service: RawObservationServiceDep, _: CurrentUser):
    return service.get_number_raw_observations()


@router.get("/{raw_observation_id}", response_model=RawObservationResponse)
def get_raw_observation(
    raw_observation_id: int,
    service: RawObservationServiceDep,
    _: CurrentUser,
):
    try:
        return service.get_raw_observation(raw_observation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=RawObservationResponse, status_code=201)
def create_raw_observation(
    raw_observation_in: RawObservationCreate,
    service: RawObservationServiceDep,
    _: CurrentUser,
):
    try:
        return service.create_raw_observation(raw_observation_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{raw_observation_id}", response_model=RawObservationResponse)
def update_raw_observation(
    raw_observation_id: int,
    raw_observation_in: RawObservationUpdate,
    service: RawObservationServiceDep,
    _: CurrentUser,
):
    try:
        return service.update_raw_observation(raw_observation_id, raw_observation_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{raw_observation_id}", status_code=204)
def delete_raw_observation(
    raw_observation_id: int,
    service: RawObservationServiceDep,
    _: CurrentUser,
):
    try:
        service.delete_raw_observation(raw_observation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
