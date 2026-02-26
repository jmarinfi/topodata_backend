from typing import Any, Generic, Optional, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Clase base para implementar repositorios con operaciones CRUD comunes."""

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get(self, id: Any) -> Optional[ModelType]:
        """Obtiene un registro por su ID."""
        return self.session.get(self.model, id)

    def get_all(self) -> Sequence[ModelType]:
        """Obtiene todos los registros."""
        return self.session.scalars(select(self.model)).all()

    def count(self) -> int:
        """Cuenta el número de registros en la tabla."""
        result = self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    def create(self, attributes: dict[str, Any]) -> ModelType:
        """Crea un nuevo registro a partir de un diccionario de atributos."""
        db_obj = self.model(**attributes)
        self.session.add(db_obj)
        self.session.flush()
        self.session.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Actualiza un registro existente con nuevos atributos."""
        for key, value in attributes.items():
            setattr(db_obj, key, value)
        self.session.flush()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        """Elimina un registro."""
        self.session.delete(db_obj)
        self.session.flush()
