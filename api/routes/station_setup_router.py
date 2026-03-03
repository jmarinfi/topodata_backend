from fastapi import APIRouter, HTTPException

from api.dependencies import StationSetupServiceDep
from api.schemas import StationSetupCreate, StationSetupResponse, StationSetupUpdate

router = APIRouter(prefix="/api/v1/station-setups", tags=["station_setups"])


@router.get("/", response_model=list[StationSetupResponse])
def get_station_setups(
    service: StationSetupServiceDep, import_session_id: int | None = None
):
    if import_session_id is not None:
        return service.get_station_setups_by_import_session(import_session_id)
    return service.get_station_setups()


@router.get("/count", response_model=int)
def get_number_station_setups(service: StationSetupServiceDep):
    return service.get_number_station_setups()


@router.get("/{station_setup_id}", response_model=StationSetupResponse)
def get_station_setup(station_setup_id: int, service: StationSetupServiceDep):
    try:
        return service.get_station_setup(station_setup_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=StationSetupResponse, status_code=201)
def create_station_setup(
    station_setup_in: StationSetupCreate, service: StationSetupServiceDep
):
    try:
        return service.create_station_setup(station_setup_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{station_setup_id}", response_model=StationSetupResponse)
def update_station_setup(
    station_setup_id: int,
    station_setup_in: StationSetupUpdate,
    service: StationSetupServiceDep,
):
    try:
        return service.update_station_setup(station_setup_id, station_setup_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{station_setup_id}", status_code=204)
def delete_station_setup(station_setup_id: int, service: StationSetupServiceDep):
    try:
        service.delete_station_setup(station_setup_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
