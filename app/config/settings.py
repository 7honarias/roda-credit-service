from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/roda_db"
    ALGORITHM: str = "HS256"

    API_TITLE: str = "Credit Service API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Gestión de créditos"

    USER_SERVICE_URL: str
    VEHICLE_SERVICE_URL: str
    SERVICE_TOKEN: str

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30 

    APP_NAME: str = "Roda Credit Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://roda.com"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()