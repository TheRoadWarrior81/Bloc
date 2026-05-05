from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    ENVIRONMENT: str = "development"
    RATE_LIMIT: str = "5/minute"
    SENTRY_DSN: str = ""
    GEMINI_API_KEY: str = ""
    DB_URL_DIRECT: str = ""

    class Config:
        env_file = ".env"

settings = Settings()