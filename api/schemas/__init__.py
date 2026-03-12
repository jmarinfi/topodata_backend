from typing import Annotated, Union

from pydantic import Field

from api.schemas.approximate_coordinate_schemas import (
    ApproximateCoordinateCreate,
    ApproximateCoordinateResponse,
    ApproximateCoordinateUpdate,
)
from api.schemas.bessel_observation_schemas import (
    BesselObservationCreate,
    BesselObservationResponse,
    BesselObservationUpdate,
)
from api.schemas.coordinate_schemas import (
    CoordinateCreate,
    CoordinateResponse,
    CoordinateUpdate,
)
from api.schemas.import_session_schemas import (
    ImportSessionCreate,
    ImportSessionResponse,
    ImportSessionUpdate,
)
from api.schemas.parser_schemas import GkaImportResult
from api.schemas.project_schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from api.schemas.raw_observaton_schemas import (
    RawObservationCreate,
    RawObservationParsed,
    RawObservationResponse,
    RawObservationUpdate,
)
from api.schemas.reference_coordinate_schemas import (
    ReferenceCoordinateCreate,
    ReferenceCoordinateResponse,
    ReferenceCoordinateUpdate,
)
from api.schemas.station_setup_schemas import (
    StationSetupCreate,
    StationSetupParsed,
    StationSetupResponse,
    StationSetupUpdate,
)

AnyCoordinateResponse = Annotated[
    Union[
        ReferenceCoordinateResponse, ApproximateCoordinateResponse, CoordinateResponse
    ],
    Field(discriminator="type"),
]

__all__ = [
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ImportSessionCreate",
    "ImportSessionResponse",
    "ImportSessionUpdate",
    "StationSetupCreate",
    "StationSetupParsed",
    "StationSetupResponse",
    "StationSetupUpdate",
    "RawObservationCreate",
    "RawObservationParsed",
    "RawObservationResponse",
    "RawObservationUpdate",
    "BesselObservationCreate",
    "BesselObservationResponse",
    "BesselObservationUpdate",
    "CoordinateCreate",
    "CoordinateResponse",
    "CoordinateUpdate",
    "ReferenceCoordinateCreate",
    "ReferenceCoordinateResponse",
    "ReferenceCoordinateUpdate",
    "ApproximateCoordinateCreate",
    "ApproximateCoordinateResponse",
    "ApproximateCoordinateUpdate",
    "AnyCoordinateResponse",
    "GkaImportResult",
]
