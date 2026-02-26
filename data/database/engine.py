from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./database/dev.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Generador de sesiones de base de datos."""
    with SessionLocal() as db:
        yield db


# Alias reutilizable para inyectar en routers y factories
SessionDep = Annotated[Session, Depends(get_db)]
