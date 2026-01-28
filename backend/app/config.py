from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "ScoreScan"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./storage/scorescan.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_reset_token_expire_hours: int = 24

    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "ScoreScan"
    frontend_url: str = "http://localhost:5173"

    # Storage
    storage_path: str = "./storage"
    max_upload_size_mb: int = 50
    allowed_extensions: List[str] = ["png", "jpg", "jpeg", "pdf", "tiff", "tif"]

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # External tools
    audiveris_path: str = "/opt/audiveris/bin/Audiveris"
    musescore_path: str = "/usr/local/bin/musescore"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def upload_path(self) -> str:
        return os.path.join(self.storage_path, "uploads")

    @property
    def musicxml_path(self) -> str:
        return os.path.join(self.storage_path, "musicxml")

    @property
    def pdf_path(self) -> str:
        return os.path.join(self.storage_path, "pdf")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
