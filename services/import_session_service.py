from api.schemas import ImportSessionCreate, ImportSessionResponse, ImportSessionUpdate
from data.repositories import ImportSessionRepository, ProjectRepository


class ImportSessionService:
    """Servicio para la gestión de sesiones de importación."""

    def __init__(
        self, repository: ImportSessionRepository, repository_project: ProjectRepository
    ) -> None:
        self.repository = repository
        self.repository_project = repository_project

    def get_import_sessions(self) -> list[ImportSessionResponse]:
        import_sessions = self.repository.get_all()
        return [
            ImportSessionResponse.model_validate(import_session)
            for import_session in import_sessions
        ]

    def get_import_sessions_by_project(
        self, project_id: int
    ) -> list[ImportSessionResponse]:
        import_sessions = self.repository.get_by_project(project_id)
        return [
            ImportSessionResponse.model_validate(import_session)
            for import_session in import_sessions
        ]

    def get_import_session(self, import_session_id: int) -> ImportSessionResponse:
        import_session = self.repository.get(import_session_id)
        if not import_session:
            raise ValueError(
                f"Sesión de importación con id {import_session_id} no encontrada."
            )
        return ImportSessionResponse.model_validate(import_session)

    def get_number_import_sessions(self) -> int:
        return self.repository.count()

    def create_import_session(
        self, import_session_data: ImportSessionCreate
    ) -> ImportSessionResponse:
        project = self.repository_project.get(import_session_data.project_id)
        if not project:
            raise ValueError(
                f"Proyecto con id {import_session_data.project_id} no encontrado."
            )

        existing_import = self.repository.get_by_project_and_hash(
            import_session_data.project_id, import_session_data.content_hash
        )
        if existing_import:
            raise ValueError(
                f"Ya existe esta sesión de importación para el proyecto {import_session_data.project_id}."
            )

        attributes = import_session_data.model_dump()
        import_session = self.repository.create(attributes)
        self.repository.refresh(import_session)
        return ImportSessionResponse.model_validate(import_session)

    def update_import_session(
        self, import_session_id: int, import_session_data: ImportSessionUpdate
    ) -> ImportSessionResponse:
        db_import_session = self.repository.get(import_session_id)
        if not db_import_session:
            raise ValueError(
                f"Sesión de importación con id {import_session_id} no encontrada."
            )
        attributes = import_session_data.model_dump()
        import_session = self.repository.update(db_import_session, attributes)
        self.repository.refresh(import_session)
        return ImportSessionResponse.model_validate(import_session)

    def delete_import_session(self, import_session_id: int) -> None:
        db_import_session = self.repository.get(import_session_id)
        if not db_import_session:
            raise ValueError(
                f"Sesión de importación con id {import_session_id} no encontrada."
            )
        self.repository.delete(db_import_session)
