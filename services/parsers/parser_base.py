from abc import ABC, abstractmethod
from typing import Any


class ParserBase(ABC):
    """Clase base abstracta para todos los parsers de archivos topográficos."""

    def __init__(self, file_content: str) -> None:
        self.file_content = file_content

        self._lines: list[str] | None = None

    @property
    def lines(self) -> list[str]:
        if self._lines is None:
            self._lines = self.file_content.splitlines()
        return self._lines

    @abstractmethod
    def parse(self) -> Any: ...
