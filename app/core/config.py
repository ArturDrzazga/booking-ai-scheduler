from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Booking AI Scheduler"
    APP_VERSION: str = "1.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()