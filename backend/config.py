from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./fleetpulse.db"
    OPENSKY_CLIENT_ID: Optional[str] = None
    OPENSKY_CLIENT_SECRET: Optional[str] = None
    FAA_NOTAM_API_KEY: Optional[str] = None
    ADMIN_API_KEY: Optional[str] = None
    APP_NAME: str = "FleetPulse"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
