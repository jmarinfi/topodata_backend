from pathlib import Path
from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./sqlite_database/dev.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def init_db() -> None:
    """Crea todas las tablas definidas en los modelos si no existen."""
    from data.database.models import Base

    Path("sqlite_database").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Generador de sesiones de base de datos."""
    with SessionLocal() as db:
        yield db


# Alias reutilizable para inyectar en routers y factories
SessionDep = Annotated[Session, Depends(get_db)]
