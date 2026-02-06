from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    device: str = "cpu"
    database_path: str = "./data/crowdcount.db"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
