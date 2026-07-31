"""Endpoints GET de coordenadas ajustadas (T10).

Tests de integración HTTP: siembra un proyecto con referencias y puntos
de control, dispara el cálculo de coordenadas aproximadas vía el endpoint
de estacionamiento, y verifica que los endpoints de coordenadas ajustadas
devuelven los registros correctos.
"""

import pytest


# Datos de referencia (iguales a test_approximate_pipeline.py).
_REF_POINTS = [
    ("C55-R-01E-C", 428175.22878, 4584168.00555, 43.50666),
    ("C55-R-02E-C", 428167.65241, 4584173.65057, 43.79948),
    ("C56-R-01S", 428268.95672, 4584021.11743, 42.2427),
    ("C56-R-02S", 428266.30794, 4584026.24574, 42.25225),
]


class TestAdjustedCoordinateEndpoints:
    """GET /api/v1/adjusted-coordinates/... con datos reales."""

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _setup_fixtures(auth_client):
        """Crea proyecto, referencias, import session, station setup,
        raw obs y Bessel obs; dispara el cálculo y devuelve los ids."""
        # Proyecto.
        r = auth_client.post(
            "/api/v1/projects/",
            json={
                "name": "Proyecto MMC Test",
                "coordinate_system": "EPSG:25830",
                "zona_utm": "30T",
                "a_elip": 6378137.0,
                "b_elip": 6356752.314,
                "f_elip": 1.0 / 298.257222101,
                "inv_f_elip": 298.257222101,
            },
        )
        assert r.status_code == 201, r.text
        project_id = r.json()["id"]

        # Referencias.
        for name, x, y, z in _REF_POINTS:
            r = auth_client.post(
                "/api/v1/reference-coordinates/",
                json={
                    "target_name": name,
                    "x": x,
                    "y": y,
                    "z": z,
                    "project_id": project_id,
                },
            )
            assert r.status_code == 201, r.text

        # Import session.
        r = auth_client.post(
            "/api/v1/import-sessions/",
            json={
                "project_id": project_id,
                "filename": "test_mmc.gka",
                "content_hash": "test_mmc_hash",
                "raw_file_content": "",
            },
        )
        assert r.status_code == 201, r.text
        import_session_id = r.json()["id"]

        # Station setup.
        r = auth_client.post(
            "/api/v1/station-setups/",
            json={
                "import_session_id": import_session_id,
                "station_name": "EST-MMC",
                "station_height": 0.0,
            },
        )
        assert r.status_code == 201, r.text
        station_setup_id = r.json()["id"]

        # Raw observations (una por cada punto, refs + controles).
        _ALL_TARGETS = [r[0] for r in _REF_POINTS] + ["CTRL-01", "CTRL-02", "CTRL-03"]
        for i, name in enumerate(_ALL_TARGETS, 1):
            r = auth_client.post(
                "/api/v1/raw-observations/",
                json={
                    "station_setup_id": station_setup_id,
                    "target_name": name,
                    "target_number": i,
                    "circle": 1,
                    "hz_angle": 0.0,
                    "v_angle": 0.0,
                    "distance_geom": 0.0,
                    "target_height": 0.0,
                },
            )
            assert r.status_code == 201, r.text

        # Bessel observaciones de referencia.
        _BESSEL_REF_DATA = [
            ("C55-R-01E-C", 116.2512, 103.5723, 115.705451),
            ("C55-R-02E-C", 115.4362, 103.1571, 125.225526),
            ("C56-R-01S", 350.6889, 107.5897, 64.695428),
            ("C56-R-02S", 352.2693, 108.2854, 59.190512),
        ]
        for name, hz, v, d in _BESSEL_REF_DATA:
            r = auth_client.post(
                "/api/v1/bessel-observations/",
                json={
                    "station_setup_id": station_setup_id,
                    "target_name": name,
                    "hz_angle_direct": 0.0,
                    "v_angle_direct": 0.0,
                    "distance_direct": 0.0,
                    "hz_angle_inverse": 0.0,
                    "v_angle_inverse": 0.0,
                    "distance_inverse": 0.0,
                    "hz_angle_bessel": hz,
                    "v_angle_bessel": v,
                    "distance_bessel": d,
                    "hz_angle_delta": 0.0,
                    "v_angle_delta": 0.0,
                    "distance_delta": 0.0,
                },
            )
            assert r.status_code == 201, r.text

        # Bessel observaciones de control.
        _CONTROL_DATA = [
            ("CTRL-01", 200.0, 100.0, 80.0),
            ("CTRL-02", 250.0, 100.0, 100.0),
            ("CTRL-03", 300.0, 100.0, 90.0),
        ]
        for name, hz, v, d in _CONTROL_DATA:
            r = auth_client.post(
                "/api/v1/bessel-observations/",
                json={
                    "station_setup_id": station_setup_id,
                    "target_name": name,
                    "hz_angle_direct": 0.0,
                    "v_angle_direct": 0.0,
                    "distance_direct": 0.0,
                    "hz_angle_inverse": 0.0,
                    "v_angle_inverse": 0.0,
                    "distance_inverse": 0.0,
                    "hz_angle_bessel": hz,
                    "v_angle_bessel": v,
                    "distance_bessel": d,
                    "hz_angle_delta": 0.0,
                    "v_angle_delta": 0.0,
                    "distance_delta": 0.0,
                },
            )
            assert r.status_code == 201, r.text

        # Disparar el cálculo de coords aproximadas (que encadena el MMC).
        r = auth_client.post(
            f"/api/v1/station-setups/{station_setup_id}/approximate-coordinates"
        )
        assert r.status_code == 200, r.text

        return station_setup_id

    # ------------------------------------------------------------------ #
    # Tests
    # ------------------------------------------------------------------ #

    def test_by_station_setup_returns_adjusted_coordinates(self, auth_client):
        station_setup_id = self._setup_fixtures(auth_client)

        r = auth_client.get(
            f"/api/v1/adjusted-coordinates/by-station-setup/{station_setup_id}"
        )
        assert r.status_code == 200

        data = r.json()
        control_names = {"CTRL-01", "CTRL-02", "CTRL-03"}
        assert len(data) == len(control_names)

        for item in data:
            assert item["target_name"] in control_names
            assert item["type"] == "adjusted"
            assert "id" in item
            assert "bessel_observation_id" in item
            assert isinstance(item["prec_x"], (int, float))
            assert isinstance(item["prec_y"], (int, float))
            assert isinstance(item["x"], (int, float))
            assert isinstance(item["y"], (int, float))
            assert isinstance(item["z"], (int, float))

    def test_get_by_id_returns_adjusted_coordinate(self, auth_client):
        station_setup_id = self._setup_fixtures(auth_client)

        # Obtener lista y luego consultar el primero por id.
        r = auth_client.get(
            f"/api/v1/adjusted-coordinates/by-station-setup/{station_setup_id}"
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0

        first = data[0]
        coord_id = first["id"]

        r = auth_client.get(f"/api/v1/adjusted-coordinates/{coord_id}")
        assert r.status_code == 200, r.text
        assert r.json() == first

    def test_get_by_id_404_for_nonexistent(self, auth_client):
        r = auth_client.get("/api/v1/adjusted-coordinates/99999")
        assert r.status_code == 404

    def test_count_returns_number_of_adjusted(self, auth_client):
        station_setup_id = self._setup_fixtures(auth_client)

        r = auth_client.get("/api/v1/adjusted-coordinates/count")
        assert r.status_code == 200
        assert r.json() >= 3

    def test_list_all_returns_adjusted_coordinates(self, auth_client):
        self._setup_fixtures(auth_client)

        r = auth_client.get("/api/v1/adjusted-coordinates/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3

        for item in data:
            assert item["type"] == "adjusted"
