"""Runtime configuration, read from environment variables."""

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    db_path:str="shortener.db"
    base_url :str=""

    @classmethod
    def from_env(cls)->"Settings":
        return cls(
            db_path = os.getenv("SHORTENER_DB_PATH",cls.db_path),
            base_url = os.getenv("SHORTENER_BASE_URL",cls.base_url).rstrip("/"),
            )