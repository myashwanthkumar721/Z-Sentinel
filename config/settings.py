from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Z-Sentinel"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    database_url: str = f"sqlite:///{BASE_DIR / 'database' / 'z_sentinel.db'}"

    data_dir: Path = BASE_DIR / "data"
    raw_data_dir: Path = BASE_DIR / "data" / "raw"
    processed_data_dir: Path = BASE_DIR / "data" / "processed"
    sample_data_dir: Path = BASE_DIR / "data" / "sample"

    model_dir: Path = BASE_DIR / "models"
    log_dir: Path = BASE_DIR / "logs"

    allow_threshold: float = 40.0
    verify_threshold: float = 70.0

    stream_interval_seconds: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

for directory in (
    settings.data_dir,
    settings.raw_data_dir,
    settings.processed_data_dir,
    settings.sample_data_dir,
    settings.model_dir,
    settings.log_dir,
    BASE_DIR / "database",
):
    directory.mkdir(parents=True, exist_ok=True)