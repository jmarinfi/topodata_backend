import hashlib
from dataclasses import dataclass

from api.schemas import (
    ImportSessionResponse,
    RawObservationResponse,
    StationSetupResponse,
)
from data.repositories import (
    ImportSessionRepository,
    RawObservationRepository,
    StationSetupRepository,
)
from services.parsers.gka_parser import GkaParser


@dataclass
class GkaImportResult:
    import_session: ImportSessionResponse
    station_setups: list[StationSetupResponse]
    raw_observations: list[RawObservationResponse]


class ImportOrchestratorService:
    def __init__(
        self,
        import_repo: ImportSessionRepository,
        station_repo: StationSetupRepository,
        obs_repo: RawObservationRepository,
    ):
        self.import_repo = import_repo
        self.station_repo = station_repo
        self.obs_repo = obs_repo

    def process_gka_import(
        self, project_id: int, filename: str, file_content: str
    ) -> GkaImportResult:
        parser = GkaParser(file_content)
        parsed_data = parser.parse()

        content_hash = hashlib.sha256(file_content.encode("utf-8")).hexdigest()

        existing = self.import_repo.get_by_project_and_hash(project_id, content_hash)
        if existing:
            raise ValueError(
                f"Este archivo ya fue importado en el proyecto {project_id} "
                f"(sesión {existing.id}, {existing.filename}). "
                f"Puedes importarlo en otro proyecto distinto."
            )

        import_session = self.import_repo.create(
            {
                "project_id": project_id,
                "filename": filename,
                "content_hash": content_hash,
                "raw_file_content": file_content,
            }
        )

        station_setups: list[StationSetupResponse] = []
        raw_observations: list[RawObservationResponse] = []

        for block in parsed_data:
            station_dict = block.station.model_dump()
            station_dict["import_session_id"] = import_session.id
            station = self.station_repo.create(station_dict)
            station_setups.append(StationSetupResponse.model_validate(station))

            for obs in block.raw_observations:
                obs_dict = obs.model_dump()
                obs_dict["station_setup_id"] = station.id
                raw_observation = self.obs_repo.create(obs_dict)
                raw_observations.append(
                    RawObservationResponse.model_validate(raw_observation)
                )

        return GkaImportResult(
            import_session=ImportSessionResponse.model_validate(import_session),
            station_setups=station_setups,
            raw_observations=raw_observations,
        )
