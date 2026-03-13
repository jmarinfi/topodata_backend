from api.schemas.raw_observaton_schemas import RawObservationResponse
from api.schemas.station_setup_schemas import StationSetupResponse
from data.database.engine import SessionLocal
from data.repositories.raw_observation_repository import RawObservationRepository
from data.repositories.station_setup_repository import StationSetupRepository
from services.calculations.bessel_adjuster import BesselAdjuster


def test_bessel_calculation(import_session_id: int = 1) -> None:
    with SessionLocal() as session:
        station_repo = StationSetupRepository(session=session)
        observation_repo = RawObservationRepository(session=session)

        station_setups = station_repo.get_by_import_session(import_session_id)

        if not station_setups:
            print(f"No station setups found for import_session_id={import_session_id}")
            return

        for station_setup in station_setups:
            print(f"Testing station: {station_setup.station_name}")

            raw_observations = observation_repo.get_by_station_setup(station_setup.id)
            print(f"Found {len(raw_observations)} observations")

            station_response = StationSetupResponse.model_validate(station_setup)
            observation_responses = [
                RawObservationResponse.model_validate(obs) for obs in raw_observations
            ]

            adjuster = BesselAdjuster(
                station_setup=station_response, raw_observations=observation_responses
            )
            bessel_observations = adjuster.adjust_bessel()
            for bessel_observation in bessel_observations:
                print(bessel_observation)


if __name__ == "__main__":
    test_bessel_calculation(import_session_id=1)
