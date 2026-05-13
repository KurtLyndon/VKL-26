from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    agent_app_name: str = Field(default="HLT Nmap Agent", alias="AGENT_APP_NAME")
    agent_host: str = Field(default="0.0.0.0", alias="AGENT_HOST")
    agent_port: int = Field(default=8081, alias="AGENT_PORT")
    agent_public_host: str | None = Field(default=None, alias="AGENT_PUBLIC_HOST")
    agent_public_ip: str | None = Field(default=None, alias="AGENT_PUBLIC_IP")
    agent_code: str = Field(default="AG-NMAP-01", alias="AGENT_CODE")
    agent_id: int | None = Field(default=None, alias="AGENT_ID")
    agent_version: str = Field(default="0.2.0", alias="AGENT_VERSION")
    backend_base_url: str = Field(default="http://127.0.0.1:8000", alias="BACKEND_BASE_URL")
    backend_timeout_seconds: int = Field(default=20, alias="BACKEND_TIMEOUT_SECONDS")
    nmap_agent_mode: str = Field(default="mock", alias="NMAP_AGENT_MODE")
    nmap_bin: str = Field(default="nmap", alias="NMAP_BIN")
    pkt_scanner_script_path: str = Field(
        default="task_scripts/nmap/pkt_scannerv1.py",
        alias="PKT_SCANNER_SCRIPT_PATH",
    )
    pkt_scanner_output_root: str = Field(default="agent_runs/nmap", alias="PKT_SCANNER_OUTPUT_ROOT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def normalized_backend_base_url(self) -> str:
        return self.backend_base_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
