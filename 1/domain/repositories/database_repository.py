from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.database_info import DatabaseInfo


class DatabaseRepository(ABC):
    """Абстрактный репозиторий для работы с БД"""
    
    @abstractmethod
    async def get_version(self) -> Optional[DatabaseInfo]:
        """Получить информацию о версии БД"""
        pass
    
