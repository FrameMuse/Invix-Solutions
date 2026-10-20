from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    bot_token: str = ""
    bot_mode: Literal["webhook", "polling"] = "polling"
    bot_webhook_base_url: str = ""
    bot_webhook_secret: str = ""
    admin_telegram_ids: str = ""
    admin_telegram_usernames: str = ""
    webapp_url: str = "http://localhost:13000"
    api_url: str = "http://localhost:18000"
    service_token: str = "dev-service-token"
    database_url: str = "postgresql+asyncpg://invix:invix@localhost:55432/invix"
    http_port: int = 8080

    @property
    def admin_ids(self) -> frozenset[int]:
        ids: set[int] = set()
        for raw in self.admin_telegram_ids.split(","):
            value = raw.strip()
            if not value:
                continue
            try:
                ids.add(int(value))
            except ValueError as error:
                raise ValueError(f"Invalid Telegram ID: {value}") from error
        return frozenset(ids)

    @property
    def admin_usernames(self) -> frozenset[str]:
        usernames: set[str] = set()
        for raw in self.admin_telegram_usernames.split(","):
            value = raw.strip().lstrip("@").casefold()
            if value:
                usernames.add(value)
        return frozenset(usernames)

    @property
    def asyncpg_dsn(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
