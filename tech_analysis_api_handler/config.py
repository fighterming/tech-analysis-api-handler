from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cache
from pandas import DateOffset
from sqlalchemy.orm import Session

from . import database


class DatabaseSecrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SQL_",
        env_ignore_empty=True,
        extra=None,
    )
    URI: str


class APISecrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="API_",
        env_ignore_empty=True,
        extra=None,
    )

    USERNAME: str
    PASSWORD: str


class Schemas(BaseSettings):
    CONFIG: str = "config"
    OHLC: str = "ml_ohlc"
    OHLC_D: str = "ml_ohlc_D"
    TICK: str = "ml_tickhist"


class DatabaseSettings(BaseSettings):
    secrets: DatabaseSecrets = DatabaseSecrets()
    DB_NAME: str = "ed_fetcher"
    schemas: Schemas = Schemas()


class Endpoints(BaseSettings):
    SNAPSHOT: str = "/snapshot"
    SHUTDOWN: str = "/shutdown"
    RESTART: str = "/restart"
    INFO: str = "/info"
    CONNECT: str = "/connect"
    SERVICE: str = "/service"
    SUBSCRIPTION: str = "/sub"
    SUBSCRIPTIONS: str = "/subs"
    SYMBOLS: str = "/symbols"
    HISTORY: str = "/hist"
    OHLC: str = "/ohlc"
    OHLC_D: str = "/ohlcd"
    TICK: str = "/tick"


class OHLCRuntime_(BaseSettings):
    IS_ACTIVE: bool = False
    UPDATING_SYMBOL: str | None = None


class Service(BaseSettings):
    OHLCRuntime: OHLCRuntime_ = OHLCRuntime_()


class TAModulesSettings(BaseSettings):
    PREFIX: str = "/ta"
    endpoints: Endpoints = Endpoints()
    secrets: APISecrets = APISecrets()
    STARTDATE_OFFSET: DateOffset = DateOffset(weeks=1)
    service: Service = Service()


class Settings(BaseSettings):
    # 資料庫連線設定
    name: str = "masterlink_ta"
    prefix: str = "ml_"
    endpoints: Endpoints = Endpoints()
    database: DatabaseSettings = DatabaseSettings()
    modules_ta: TAModulesSettings = TAModulesSettings()


@cache
def get_settings():
    return Settings()
