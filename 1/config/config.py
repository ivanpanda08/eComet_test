import os
from dotenv import load_dotenv

load_dotenv()

class PostgresDBConfig:
    """Конфигурация подключения к PostgreSQL"""
    
    def __init__(self):
        self.host: str = os.getenv("DB_HOST", "localhost")
        self.port: int = int(os.getenv("DB_PORT", "5432"))
        self.database: str = os.getenv("DB_NAME", "db")
        self.user: str = os.getenv("DB_USER", "user")
        self.password: str = os.getenv("DB_PASSWORD", "password")
        self.pool_min_size: int = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
        self.pool_max_size: int = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
        self.command_timeout: int | None = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
    
    @property
    def dsn_safe(self) -> str:
        """Возвращает строку подключения к БД без пароля (для логирования)"""
        return f"postgresql://{self.user}:***@{self.host}:{self.port}/{self.database}"

    @property
    def _dsn(self) -> str:
        """Возвращает полную строку подключения к БД"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    


class AppConfig:
    """Конфигурация приложения"""

    def __init__(self):
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.app_port: int = int(os.getenv("APP_PORT", "8000"))
        self.app_host: str = os.getenv("APP_HOST", "0.0.0.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

def get_app_config() -> AppConfig:
    """Функция для получения конфигурации приложения"""
    return AppConfig()


def get_db_config() -> PostgresDBConfig:
    """Функция для получения конфигурации базы данных"""
    return PostgresDBConfig()