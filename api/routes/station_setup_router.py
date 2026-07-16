from fastapi import APIRouter, HTTPException

from api.dependencies import (
    ApproximateCoordinateServiceDep,
    CurrentUser,
    StationSetupServiceDep,
)
from api.schemas import (
    ApproximateCoordinateResponse,
    StationSetupCreate,
    StationSetupResponse,
    StationSetupUpdate,
)

router = APIRouter(prefix="/api/v1/station-setups", tags=["station-setups"])


@router.get("/", response_model=list[StationSetupResponse])
def get_station_setups(
    service: StationSetupServiceDep,
    _: CurrentUser,
    import_session_id: int | None = None,
):
    if import_session_id is not None:
        return service.get_station_setups_by_import_session(import_session_id)
    return service.get_station_setups()


@router.get("/count", response_model=int)
def get_number_station_setups(service: StationSetupServiceDep, _: CurrentUser):
    return service.get_number_station_setups()


@router.get("/{station_setup_id}", response_model=StationSetupResponse)
def get_station_setup(
    station_setup_id: int, service: StationSetupServiceDep, _: CurrentUser
):
    try:
        return service.get_station_setup(station_setup_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=StationSetupResponse, status_code=201)
def create_station_setup(
    station_setup_in: StationSetupCreate,
    service: StationSetupServiceDep,
    _: CurrentUser,
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
    _: CurrentUser,
):
    try:
        return service.update_station_setup(station_setup_id, station_setup_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{station_setup_id}", status_code=204)
def delete_station_setup(
    station_setup_id: int, service: StationSetupServiceDep, _: CurrentUser
):
    try:
        service.delete_station_setup(station_setup_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{station_setup_id}/approximate-coordinates",
    response_model=list[ApproximateCoordinateResponse],
    status_code=200,
)
def calculate_approximate_coordinates(
    station_setup_id: int,
    service: ApproximateCoordinateServiceDep,
    _: CurrentUser,
):
    """Calcula y persiste las coordenadas aproximadas de un estacionamiento.

    Ejecuta el pipeline completo: inversa planimétrica de Cassini, factor
    de escala UTM, cota de la estación, desorientación y radiación de cada
    observación Bessel. Es idempotente: las coordenadas previas se borran
    y se reescriben.
    """
    try:
        result = service.calculate_for_station_setup(station_setup_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result.approximate_coordinates
