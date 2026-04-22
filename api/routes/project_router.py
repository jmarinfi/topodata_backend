from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.dependencies import (
    CurrentUser,
    ImportOrchestratorServiceDep,
    ProjectServiceDep,
)
from api.schemas import GkaImportResult, ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def get_projects(service: ProjectServiceDep, _: CurrentUser):
    return service.get_projects()


@router.get("/count", response_model=int)
def get_number_projects(service: ProjectServiceDep, _: CurrentUser):
    return service.get_number_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, service: ProjectServiceDep, _: CurrentUser):
    try:
        return service.get_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/name", response_model=str)
def get_name_project(project_id: int, service: ProjectServiceDep, _: CurrentUser):
    try:
        return service.get_name_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project_in: ProjectCreate, service: ProjectServiceDep, _: CurrentUser
):
    return service.create_project(project_in)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    service: ProjectServiceDep,
    _: CurrentUser,
):
    try:
        return service.update_project(project_id, project_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, service: ProjectServiceDep, _: CurrentUser):
    try:
        service.delete_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/import_gka/{project_id}", response_model=GkaImportResult, status_code=201
)
def import_gka(
    project_id: int,
    gka_file: Annotated[UploadFile, File()],
    service: ImportOrchestratorServiceDep,
    _: CurrentUser,
):
    if not gka_file.filename or not gka_file.filename.lower().endswith(".gka"):
        raise HTTPException(
            status_code=400, detail="El fichero debe tener extensión .gka"
        )

    try:
        file_content = gka_file.file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="El fichero debe estar codificado en UTF-8"
        )

    try:
        result = service.process_gka_import(
            project_id=project_id, filename=gka_file.filename, file_content=file_content
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
