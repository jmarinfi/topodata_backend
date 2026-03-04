from api.routes.approximate_coordinate_router import (
    router as approximate_coordinate_router,
)
from api.routes.bessel_observation_router import router as bessel_observation_router
from api.routes.import_session_router import router as import_session_router
from api.routes.project_router import router as project_router
from api.routes.raw_observation_router import router as raw_observation_router
from api.routes.reference_coordinate_router import router as reference_coordinate_router
from api.routes.station_setup_router import router as station_setup_router

__all__ = [
    "project_router",
    "import_session_router",
    "station_setup_router",
    "raw_observation_router",
    "bessel_observation_router",
    "reference_coordinate_router",
    "approximate_coordinate_router",
]
