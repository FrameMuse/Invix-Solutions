from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql+asyncpg://invix:invix@localhost:55432/invix"
    service_token: str = "dev-service-token"
    cors_origins: str = "https://framemuse.github.io,http://localhost:13000"

    s3_endpoint_url: str = "http://localhost:19000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "media"
    s3_region: str = "us-east-1"
    public_base_url: str = "http://localhost:18000"

    @property
    def asyncpg_dsn(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
