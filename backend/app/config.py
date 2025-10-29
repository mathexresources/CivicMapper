import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./mikulash.db")
    ruian_source_url: str | None = os.getenv("RUIAN_SOURCE_URL") or None
    osrm_base_url: str | None = os.getenv("OSRM_BASE_URL") or None
    gh_base_url: str | None = os.getenv("GH_BASE_URL") or None
    gh_key: str | None = os.getenv("GH_KEY") or None
    tile_style_url: str | None = os.getenv("TILE_STYLE_URL") or None

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
