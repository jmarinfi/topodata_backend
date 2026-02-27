from fastapi import APIRouter, HTTPException

from api.dependencies import ProjectServiceDep
from api.schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def get_projects(service: ProjectServiceDep):
    return service.get_projects()


@router.get("/count", response_model=int)
def get_number_projects(service: ProjectServiceDep):
    return service.get_number_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, service: ProjectServiceDep):
    try:
        return service.get_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/name", response_model=str)
def get_name_project(project_id: int, service: ProjectServiceDep):
    try:
        return service.get_name_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project_in: ProjectCreate, service: ProjectServiceDep):
    return service.create_project(project_in)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, project_in: ProjectUpdate, service: ProjectServiceDep
):
    try:
        return service.update_project(project_id, project_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, service: ProjectServiceDep):
    try:
        service.delete_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
