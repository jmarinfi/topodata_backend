from typing import Any, Generic, Optional, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Clase base para implementar repositorios con operaciones CRUD comunes."""

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self._session = session

    def get(self, id: Any) -> Optional[ModelType]:
        """Obtiene un registro por su ID."""
        return self._session.get(self.model, id)

    def get_all(self) -> Sequence[ModelType]:
        """Obtiene todos los registros."""
        return self._session.scalars(select(self.model)).all()

    def count(self) -> int:
        """Cuenta el número de registros en la tabla."""
        result = self._session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    def create(self, attributes: dict[str, Any]) -> ModelType:
        """Crea un nuevo registro a partir de un diccionario de atributos."""
        db_obj = self.model(**attributes)
        self._session.add(db_obj)
        self._session.flush()
        return db_obj

    def update(self, db_obj: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Actualiza un registro existente con nuevos atributos."""
        for key, value in attributes.items():
            setattr(db_obj, key, value)
        self._session.flush()
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        """Elimina un registro."""
        self._session.delete(db_obj)
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def refresh(self, db_obj: ModelType) -> None:
        self._session.refresh(db_obj)
