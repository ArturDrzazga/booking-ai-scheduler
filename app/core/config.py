from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Booking AI Scheduler"
    APP_VERSION: str = "1.0"

    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://booking:booking@localhost:5432/booking"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
