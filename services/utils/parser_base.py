from abc import ABC, abstractmethod


class ParserBase(ABC):
    """Clase base abstracta para todos los parsers de archivos topográficos."""

    def __init__(self, file_content: str) -> None:
        self.file_content = file_content

    @property
    def lines(self) -> list[str]:
        return self.file_content.splitlines()
