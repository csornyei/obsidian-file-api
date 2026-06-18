import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    log_level: str = "INFO"
    otel_exporter_otlp_endpoint: str = "http://alloy:4317"
    environment: str = "homelab"
    base_dir: str = os.path.dirname(os.path.abspath(__file__))


config = Config()
