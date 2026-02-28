"""Configuration for CIV-ARCOS."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8080
    db_path: str = "civ_arcos.json"
    log_level: str = "INFO"
    github_token: str = ""


_config: Config = None  # type: ignore[assignment]


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config(
            host=os.environ.get("CIV_HOST", "0.0.0.0"),
            port=int(os.environ.get("CIV_PORT", "8080")),
            db_path=os.environ.get("CIV_DB_PATH", "civ_arcos.json"),
            log_level=os.environ.get("CIV_LOG_LEVEL", "INFO"),
            github_token=os.environ.get("GITHUB_TOKEN", ""),
        )
    return _config
