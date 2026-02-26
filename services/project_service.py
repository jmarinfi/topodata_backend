from data.repositories.project_repository import ProjectRepository


class ProjectService:
    """Servicio para la gestión de proyectos."""

    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository
