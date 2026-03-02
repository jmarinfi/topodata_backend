from fastapi import APIRouter, HTTPException

from api.dependencies import ImportSessionServiceDep
from api.schemas import ImportSessionCreate, ImportSessionResponse, ImportSessionUpdate

router = APIRouter(prefix="/api/v1/import_sessions", tags=["import_sessions"])


@router.get("/", response_model=list[ImportSessionResponse])
def get_import_sessions(
    service: ImportSessionServiceDep, project_id: int | None = None
):
    if project_id is not None:
        return service.get_import_sessions_by_project(project_id)
    return service.get_import_sessions()


@router.get("/count", response_model=int)
def get_number_import_sessions(service: ImportSessionServiceDep):
    return service.get_number_import_sessions()


@router.get("/{import_session_id}", response_model=ImportSessionResponse)
def get_import_session(import_session_id: int, service: ImportSessionServiceDep):
    try:
        return service.get_import_session(import_session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ImportSessionResponse, status_code=201)
def create_import_session(
    import_session_in: ImportSessionCreate, service: ImportSessionServiceDep
):
    try:
        return service.create_import_session(import_session_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{import_session_id}", response_model=ImportSessionResponse)
def update_import_session(
    import_session_id: int,
    import_session_in: ImportSessionUpdate,
    service: ImportSessionServiceDep,
):
    try:
        return service.update_import_session(import_session_id, import_session_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{import_session_id}", status_code=204)
def delete_import_session(import_session_id: int, service: ImportSessionServiceDep):
    try:
        service.delete_import_session(import_session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
