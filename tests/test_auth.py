"""Camino crítico de auth: endpoint protegido sin token → 401, con token → 200."""


def test_protected_endpoint_without_token_is_401(client):
    response = client.get("/api/v1/projects/")

    assert response.status_code == 401


def test_protected_endpoint_with_token_is_200(auth_client):
    response = auth_client.get("/api/v1/projects/")

    assert response.status_code == 200
    # DB vacía → lista de proyectos vacía
    assert response.json() == []
