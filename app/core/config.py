from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Booking AI Scheduler"
    APP_VERSION: str = "1.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://booking:booking@localhost:5432/booking"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
