from typing import Dict
from pydantic import BaseSettings, BaseModel
from dotenv import dotenv_values
from datetime import date
from functools import lru_cache

env: Dict[str, str | None] = dotenv_values(".env")


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "app"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, dict[str, str]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict[str, dict[str, str]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


def get_api_key() -> str | None:
    key: str | None = env["RIOT_API_KEY"]
    return key


def get_db_uri() -> str | None:
    key: str | None = env["ATLAS_URI"]
    return key


def get_db_name() -> str | None:
    key: str | None = env.get("DB_NAME", "tftchamp")
    return key


def get_patch() -> date:
    patch: date = date.fromisoformat(env.get("PATCH", "2023-05-16"))
    return patch


def get_latest_release() -> str | None:
    latest_release: str | None = env.get("LATEST_RELEASE", "13.10.509.8402")
    return latest_release


class CommonSettings(BaseSettings):
    APP_NAME: str = "tftchamp"
    DEBUG_MODE: bool = False


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class Settings(CommonSettings, ServerSettings):
    app_name: str = "tft champ"
    assets_dir: str = "assets"
    db_uri: str = get_db_uri()
    db_name: str = get_db_name()
    api_key: str = get_api_key()
    patch: date = get_patch()
    latest_release: str = get_latest_release()
    targetname: str = "placement"
    max_count: int = 75
    # Regions (actually called platform) taken from https://developer.riotgames.com/docs/lol
    regions: dict = {
        "EUW1": {"code": "EUW1", "host": "euw1.api.riotgames.com"},
        "BR1": {"code": "BR1", "host": "br1.api.riotgames.com"},
        "EUN1": {"code": "EUN1", "host": "eun1.api.riotgames.com"},
        "JP1": {"code": "JP1", "host": "jp1.api.riotgames.com"},
        "KR": {"code": "KR", "host": "kr.api.riotgames.com"},
        "LA1": {"code": "LA1", "host": "la1.api.riotgames.com"},
        "LA2": {"code": "LA2", "host": "la2.api.riotgames.com"},
        "NA1": {"code": "NA1", "host": "na1.api.riotgames.com"},
        "OC1": {"code": "OC1", "host": "oc1.api.riotgames.com"},
        "TR1": {"code": "TR1", "host": "tr1.api.riotgames.com"},
        "RU": {"code": "RU", "host": "ru.api.riotgames.com"},
    }
    server: str = "na1"

    def get_api_host(self, region_code):
        if not region_code in self.regions:
            raise Exception("Region code not recognised")
        else:
            return self.regions[region_code]["host"]


settings: Settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    return settings
