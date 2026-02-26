from fastapi import APIRouter

from api.dependencies import ProjectServiceDep

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/")
def get_projects(service: ProjectServiceDep): ...
