import numpy as np
import pandas as pd

from api.schemas import (
    BesselObservationCreate,
    RawObservationResponse,
    StationSetupResponse,
)


class BesselAdjuster:
    def __init__(
        self,
        station_setup: StationSetupResponse,
        raw_observations: list[RawObservationResponse],
    ) -> None:
        self.station_setup = station_setup
        self.raw_observations = raw_observations

        self.df_observations: pd.DataFrame = self._to_df()
        self.bessel_observations: list[BesselObservationCreate]

    def _to_df(self) -> pd.DataFrame:
        if not self.raw_observations:
            raise ValueError(
                f"No hay observaciones brutas en el estacionamiento: {self.station_setup}"
            )

        return pd.DataFrame(
            [raw_observation.model_dump() for raw_observation in self.raw_observations]
        )

    def adjust_bessel(self) -> list[BesselObservationCreate]:
        if self.df_observations.empty:
            raise ValueError("No hay observaciones en el dataframe de observaciones.")

        df: pd.DataFrame = self.df_observations.loc[
            (self.df_observations["v_angle"] != 0)
            & (self.df_observations["distance_geom"] != 0)
        ].copy()
        df = df.rename(columns={"distance_geom": "distance"})

        if df.empty:
            raise ValueError(
                "No hay observaciones válidas en el dataframe de observaciones."
            )

        pivot_df = pd.pivot_table(
            df,
            index="target_name",
            columns="circle",
            values=["hz_angle", "v_angle", "distance"],
            aggfunc="mean",
        )

        pivot_df.columns = [
            f"{col[0]}_{'direct' if col[1] == 1 else 'inverse'}"
            for col in pivot_df.columns
        ]
        pivot_df = pivot_df.reset_index()

        required_cols = [
            "hz_angle_direct",
            "hz_angle_inverse",
            "v_angle_direct",
            "v_angle_inverse",
            "distance_direct",
            "distance_inverse",
        ]
        pivot_df = pivot_df.dropna(
            subset=[col for col in required_cols if col in pivot_df.columns]
        )

        if pivot_df.empty:
            raise ValueError(
                "No hay observaciones válidas con observaciones directas e inversas."
            )

        pivot_df["hz_angle_bessel"] = (
            pivot_df["hz_angle_direct"]
            + pivot_df["hz_angle_inverse"]
            + np.where(pivot_df["hz_angle_direct"] < 200, -200, 200)
        ) / 2

        pivot_df["v_angle_bessel"] = (
            pivot_df["v_angle_direct"]
            - (pivot_df["v_angle_direct"] + pivot_df["v_angle_inverse"] - 400) / 2
        )

        pivot_df["distance_bessel"] = pivot_df[
            ["distance_direct", "distance_inverse"]
        ].mean(axis=1)

        pivot_df["hz_angle_delta"] = (
            pivot_df["hz_angle_inverse"]
            - pivot_df["hz_angle_direct"]
            + np.where(pivot_df["hz_angle_direct"] < 200, -200, 200)
        )

        pivot_df["v_angle_delta"] = (
            pivot_df["v_angle_direct"] - pivot_df["v_angle_bessel"]
        ) * 2

        pivot_df["distance_delta"] = (
            pivot_df["distance_bessel"] - pivot_df["distance_direct"]
        ) * 2

        final_cols = [
            "hz_angle_bessel",
            "v_angle_bessel",
            "distance_bessel",
            "hz_angle_delta",
            "v_angle_delta",
            "distance_delta",
        ]
        pivot_df = pivot_df.dropna(subset=final_cols)

        records = pivot_df.to_dict(orient="records")
        return [
            BesselObservationCreate(station_setup_id=self.station_setup.id, **record)
            for record in records
        ]
