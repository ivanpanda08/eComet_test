from typing import Final
import os
from dotenv import load_dotenv

GITHUB_API_BASE_URL: Final[str] = "https://api.github.com"

load_dotenv()

class Config:
    def __init__(self):
        self.github_api_base_url: str = GITHUB_API_BASE_URL
        self.github_api_token: str = os.getenv("GITHUB_TOKEN")
        self.max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.requests_per_second: int = int(os.getenv("REQUESTS_PER_SECOND", "5"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

async def get_config() -> Config:
    return Config()