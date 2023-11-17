from functools import lru_cache
from typing import Optional

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv(".env"))


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    # class Config:
    #     env_file: str = f"{ENV_PATH}"
    # https://stackoverflow.com/questions/76674272/pydantic-basesettings-cant-find-env-when-running-commands-from-different-places
    model_config = SettingsConfigDict(case_sensitive=True)


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False


class DevConfig(GlobalConfig):
    class Config:
        env_prefix: str = "DEV_"


class ProdConfig(GlobalConfig):
    class Config:
        env_prefix: str = "PROD_"


class TestConfing(GlobalConfig):
    DATABASE_URL: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True

    class Config:
        env_prefix: str = "TEST_"


@lru_cache()
def get_config(env_state: str):
    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfing}
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
