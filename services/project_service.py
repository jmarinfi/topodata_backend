from api.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from data.repositories import ProjectRepository


class ProjectService:
    """Servicio para la gestión de proyectos."""

    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    def get_projects(self) -> list[ProjectResponse]:
        projects = self.repository.get_all()
        return [ProjectResponse.model_validate(project) for project in projects]

    def get_project(self, project_id: int) -> ProjectResponse:
        project = self.repository.get(project_id)
        if not project:
            raise ValueError(f"Proyecto con id {project_id} no encontrado.")
        return ProjectResponse.model_validate(project)

    def get_number_projects(self) -> int:
        return self.repository.count()

    def get_name_project(self, project_id: int) -> str:
        project = self.repository.get(project_id)
        if not project:
            raise ValueError(f"Proyecto con id {project_id} no encontrado.")
        return project.name

    def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        attributes = project_data.model_dump()
        project = self.repository.create(attributes)
        self.repository.refresh(project)
        return ProjectResponse.model_validate(project)

    def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> ProjectResponse:
        db_project = self.repository.get(project_id)
        if not db_project:
            raise ValueError(f"Proyecto con id {project_id} no encontrado.")
        attributes = project_data.model_dump()
        project = self.repository.update(db_project, attributes)
        self.repository.refresh(project)
        return ProjectResponse.model_validate(project)

    def delete_project(self, project_id: int) -> None:
        db_project = self.repository.get(project_id)
        if not db_project:
            raise ValueError(f"Proyecto con id {project_id} no encontrado.")
        self.repository.delete(db_project)
