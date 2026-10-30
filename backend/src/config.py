import os
from typing import List


class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "crm_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "crm_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "crm_password")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "default_secret_key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "default_jwt_secret")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")]

    SCRAPER_CONCURRENCY_LIMIT: int = int(os.getenv("SCRAPER_CONCURRENCY_LIMIT", "1"))
    SCRAPER_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("SCRAPER_REQUEST_TIMEOUT_SECONDS", "30"))
    SCRAPER_USER_AGENT: str = os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "180"))

    @property
    def postgres_conninfo(self) -> str:
        return (
            f"host={self.POSTGRES_HOST} port={self.POSTGRES_PORT} dbname={self.POSTGRES_DB} "
            f"user={self.POSTGRES_USER} password={self.POSTGRES_PASSWORD} connect_timeout=5"
        )


settings = Settings()
