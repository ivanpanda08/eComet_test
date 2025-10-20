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
        self.min_size: int = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
        self.max_size: int = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
        self.command_timeout: int | None = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
    


class AppConfig:
    """Конфигурация приложения"""

    def __init__(self):
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.app_port: int = int(os.getenv("APP_PORT", "8000"))
        self.app_host: str = os.getenv("APP_HOST", "0.0.0.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")