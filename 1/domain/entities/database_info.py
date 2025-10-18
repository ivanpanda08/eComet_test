from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseInfo:
    """Сущность информации о базе данных"""
    version: str
    
    def __post_init__(self):
        if not self.version:
            raise ValueError("Версия базы данных не может быть пустой")
