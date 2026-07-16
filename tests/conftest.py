"""Fixtures compartidas: DB SQLite efímera en memoria + cliente autenticado.

Toda la API lee la sesión a través de ``data.database.engine.get_db``; sobreescribir
ese único punto (`app.dependency_overrides`) aísla los tests de ``dev.db`` sin tocar
código de producción.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import data.database.models  # noqa: F401  — registra todos los modelos en Base.metadata
from data.database.engine import get_db
from data.database.models import Base
from main import app

# SQLite en memoria con StaticPool: una sola conexión compartida por todas las
# sesiones, así las tablas creadas por ``create_all`` persisten entre peticiones.
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(_test_engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture()
def db_session():
    """Sesion directa sobre la DB de test, para tests a nivel de servicio."""
    Base.metadata.create_all(_test_engine)
    session = _TestSessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        Base.metadata.drop_all(_test_engine)


@pytest.fixture()
def client():
    """TestClient con la DB aislada y ``get_db`` sobreescrito."""
    Base.metadata.create_all(_test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(_test_engine)


@pytest.fixture()
def auth_client(client):
    """``client`` con un usuario registrado y cabecera ``Authorization`` ya puesta."""
    credentials = {
        "username": "tester",
        "email": "tester@example.com",
        "password": "supersecret",
    }
    client.post("/api/v1/auth/register", json=credentials)
    token = client.post(
        "/api/v1/auth/login", json=credentials
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
