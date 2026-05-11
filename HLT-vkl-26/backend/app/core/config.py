from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = Field(default="HLT VKL 26 API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="root", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="hlt_vkl_26", alias="MYSQL_DATABASE")
    auto_apply_migrations: bool = Field(default=False, alias="AUTO_APPLY_MIGRATIONS")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    scheduler_enabled: bool = Field(default=False, alias="SCHEDULER_ENABLED")
    scheduler_poll_seconds: int = Field(default=60, alias="SCHEDULER_POLL_SECONDS")
    worker_enabled: bool = Field(default=False, alias="WORKER_ENABLED")
    worker_poll_seconds: int = Field(default=20, alias="WORKER_POLL_SECONDS")
    agent_monitor_enabled: bool = Field(default=True, alias="AGENT_MONITOR_ENABLED")
    agent_monitor_poll_seconds: int = Field(default=60, alias="AGENT_MONITOR_POLL_SECONDS")
    agent_status_stale_seconds: int = Field(default=90, alias="AGENT_STATUS_STALE_SECONDS")
    agent_dispatch_mode: str = Field(default="auto", alias="AGENT_DISPATCH_MODE")
    agent_request_timeout_seconds: int = Field(default=20, alias="AGENT_REQUEST_TIMEOUT_SECONDS")
    auth_secret_key: str = Field(default="hlt-vkl-26-dev-secret", alias="AUTH_SECRET_KEY")
    auth_token_ttl_hours: int = Field(default=12, alias="AUTH_TOKEN_TTL_HOURS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> URL:
        return URL.create(
            "mysql+pymysql",
            username=self.mysql_user,
            password=self.mysql_password,
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
            query={"charset": "utf8mb4"},
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
