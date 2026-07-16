from dataclasses import dataclass

from gps_time import GPSTime
from pydantic import ValidationError

from api.schemas import RawObservationParsed, StationSetupParsed
from services.parsers.parser_base import ParserBase
from services.parsers.utils.parsers_utils import (
    get_float,
    get_int,
    get_req_float,
    get_req_int,
    get_req_str,
)


@dataclass
class GkaParserResult:
    station: StationSetupParsed
    raw_observations: list[RawObservationParsed]


class GkaParser(ParserBase):
    """Parsea archivos GKA. Extrae configuraciones de estacionamientos y observaciones."""

    def _parse_station_setup(self, columns: list[str]) -> StationSetupParsed:
        # P_tach, Tachname, orient, nsatzr, nsatzz, h_tach, I_extach, EX_tach, EY_tach, EZ_tach, ori, J,N,	nWeatherFlag, nBattery
        # 38110002,S01,0,0,0,0.00000000,1,,,,0.0,278.77885605,80.65533842,1,143

        current_station = StationSetupParsed(
            station_name=get_req_str(columns, 1),
            station_height=get_float(columns, 5),
            edm_refractive_index=get_float(columns, 11),
            edm_carrier_wavelength=get_float(columns, 12),
        )

        return current_station

    def _parse_raw_observation(self, columns: list[str]) -> RawObservationParsed:
        # P_targ, Targname, GPS_ww, GPS_d, GPS_ss, nSatz, npos, s, ss, h_s, r, sr, z, sz, h_z, sadd, refr, bre, I_extar, EX_tar, EY_tar, EZ_tar, dTrunnion, dSighting, nErrorFlag, dPreasure, dTemperature, dSignalstrength, nAutoLockMode, nPrismNr, nTargetID, bDR
        # 1,S01-R01,2392,3,331250.94,1,1,34.07945,0.00103,0.000,188.6212,0.00020000,102.5240,0.00020000,0.000,-0.017,0.142,0.0,1,426898.406,4583365.723,40.988,0.0420,0.0014,0,1013.20,22.50,,3,,,0

        gps_week = get_int(columns, 2)
        gps_tow = get_float(columns, 4)

        obs_time = None
        if gps_week is not None and gps_tow is not None:
            obs_time = GPSTime(week_number=gps_week, time_of_week=gps_tow).to_datetime()

        current_observation = RawObservationParsed(
            target_name=get_req_str(columns, 1),
            target_number=get_req_int(columns, 0),
            circle=get_req_int(columns, 6),
            hz_angle=get_req_float(columns, 10),
            v_angle=get_req_float(columns, 12),
            distance_geom=get_req_float(columns, 7),
            observation_time=obs_time,
            prism_constant=get_float(columns, 15),
            target_height=get_float(columns, 9),
            temperature=get_float(columns, 26),
            pressure=get_float(columns, 25),
            refraction_coef=get_float(columns, 16),
            std_dev_hz=get_float(columns, 11),
            std_dev_v=get_float(columns, 13),
            std_dev_dist=get_float(columns, 8),
        )

        return current_observation

    def parse(self) -> list[GkaParserResult]:
        """Parsea el archivo GKA y devuelve una lista de diccionarios."""
        parsed_data: list[GkaParserResult] = []
        current_observations: list[RawObservationParsed] = []
        current_station: StationSetupParsed | None = None
        is_new_station = False

        # `enumerate` con `start=1` para que el número de línea que reportamos
        # en los errores coincida con el que ve el usuario en un editor de texto
        # (los editores cuentan desde 1).
        for line_number, line in enumerate(self.lines, start=1):
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            if line.startswith("#GNV11"):
                if current_station is not None:
                    parsed_data.append(
                        GkaParserResult(current_station, current_observations)
                    )

                is_new_station = True
                current_station = None
                current_observations = []
                continue

            if line.startswith("#END11"):
                is_new_station = False
                continue

            columns = line.split(",")

            try:
                if is_new_station:
                    if len(columns) >= 2:
                        current_station = self._parse_station_setup(columns)
                        is_new_station = False
                        continue

                if current_station is not None and len(columns) >= 15:
                    raw_observation = self._parse_raw_observation(columns)
                    if raw_observation:
                        current_observations.append(raw_observation)

            except (ValueError, ValidationError) as e:
                # Formato deliberadamente estable (línea + contenido + causa en
                # líneas separadas, prefijos "Error en la línea N:" y "Causa:")
                # para que el frontend pueda parsearlo con una regex.
                raise ValueError(
                    f"Error en la línea {line_number}:\n"
                    f"  {line}\n"
                    f"Causa: {str(e)}"
                ) from e

        if current_station is not None:
            parsed_data.append(GkaParserResult(current_station, current_observations))

        return parsed_data
