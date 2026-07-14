from fastapi import APIRouter, HTTPException

from api.dependencies import CurrentUser, BesselObservationServiceDep
from api.schemas import (
    BesselObservationCreate,
    BesselObservationResponse,
    BesselObservationUpdate,
)

router = APIRouter(prefix="/api/v1/bessel-observations", tags=["bessel-observations"])


@router.get("/", response_model=list[BesselObservationResponse])
def get_bessel_observations(
    service: BesselObservationServiceDep,
    _: CurrentUser,
    station_setup_id: int | None = None,
):
    if station_setup_id:
        return service.get_bessel_observations_by_station_setup(station_setup_id)
    return service.get_bessel_observations()


@router.get("/count", response_model=int)
def get_number_bessel_observations(
    service: BesselObservationServiceDep,
    _: CurrentUser,
):
    return service.get_number_bessel_observations()


@router.get("/{bessel_observation_id}", response_model=BesselObservationResponse)
def get_bessel_observation(
    bessel_observation_id: int, service: BesselObservationServiceDep, _: CurrentUser
):
    try:
        return service.get_bessel_observation(bessel_observation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=BesselObservationResponse, status_code=201)
def create_bessel_observation(
    bessel_observation_in: BesselObservationCreate,
    service: BesselObservationServiceDep,
    _: CurrentUser,
):
    try:
        return service.create_bessel_observation(bessel_observation_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{bessel_observation_id}", response_model=BesselObservationResponse)
def update_bessel_observation(
    bessel_observation_id: int,
    bessel_observation_in: BesselObservationUpdate,
    service: BesselObservationServiceDep,
    _: CurrentUser,
):
    try:
        return service.update_bessel_observation(
            bessel_observation_id, bessel_observation_in
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{bessel_observation_id}", status_code=204)
def delete_bessel_observation(
    bessel_observation_id: int, service: BesselObservationServiceDep, _: CurrentUser
):
    try:
        service.delete_bessel_observation(bessel_observation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
