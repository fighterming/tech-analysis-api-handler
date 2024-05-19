import os
import logging
from datetime import datetime
from typing import Literal
from dataclasses import dataclass
from sqlalchemy import (
    create_engine,
    Engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Table,
    MetaData,
    Select,
    inspect,
    insert,
    exc,
    DateTime,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as sqlite_insert
from sqlalchemy.ext.declarative import declarative_base

from tech_analysis_api_handler import config

logger = logging.getLogger("src")
Base = declarative_base()
root_settings = config.Settings()
settings = root_settings.database


class OHLCTable:
    @classmethod
    def create(cls, db: Session, table_name: str):
        table = cls.get(table_name)
        table.create(db.bind, checkfirst=True)

    @staticmethod
    def get(table_name: str, metadata: MetaData = None) -> Table:
        if metadata is None:
            metadata = MetaData(schema=settings.schemas.OHLC)
        return Table(
            table_name,
            metadata,
            Column("datetime", DateTime, unique=True, nullable=False),
            Column("Date", Integer, index=True),
            Column("Product", String(20)),
            Column("TimeSn", Integer, index=True),
            Column("TimeSn_Dply", Integer),
            Column("Quantity", Integer),
            Column("Volume", Integer),
            Column("OPrice", Float),
            Column("HPrice", Float),
            Column("LPrice", Float),
            Column("CPrice", Float),
        )

    @classmethod
    def insert(cls, db: Session, data: list[dict]) -> None:
        table_name = data[0]["Product"]
        if not table_name:
            raise SyntaxError(f"No product name found in {data}")
        table = cls.get(table_name)
        table.create(db.bind, checkfirst=True)
        stmt = table.insert().values(data)
        db.execute(stmt)
        db.commit()

    @classmethod
    def insert_ignore(cls, db: Session, data: list[dict]) -> None:
        table_name = data[0]["Product"]
        if not table_name:
            raise SyntaxError(f"No product name found in {data}")
        table = cls.get(table_name)
        table.create(db.bind, checkfirst=True)
        if db.bind.dialect.name in ["mysql", "mariadb"]:
            stmt = table.insert().prefix_with("IGNORE")
            db.execute(stmt, data)
        elif db.bind.dialect.name in ["sqlite", "postgresql"]:
            stmt = sqlite_insert(table).on_conflict_do_nothing(
                index_elements=[table.c.datetime]
            )
            stmt = stmt.values(data)
            db.execute(stmt)
        db.commit()


def get_db() -> type[Session]:
    uri = settings.secrets.URI
    db_name = settings.DB_NAME
    engine = create_engine(f"{uri}/{db_name}")
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_latest_datetime(session: Session, table: Table):
    lastest_row = (
        session.query(table).order_by(table.c.datetime.desc()).limit(1).first()
    )
    return lastest_row.datetime if lastest_row else None


def table_exist(session: Session, table_name: str) -> bool:
    inspector = inspect(session.bind)
    return table_name in inspector.get_table_names()


class TASqldb:
    def __init__(self, server_name: Literal["local", "remote"], db_name: str):
        if server_name == "local":
            create_engine_ = TASqldb.create_local_engine
        elif server_name == "remote":
            create_engine_ = TASqldb.create_remote_engine
        self.__engine__ = create_engine_(db_name)
        self.__server_name__ = server_name
        self.__database__ = db_name

    def create_session(self) -> Session:
        Session = sessionmaker(bind=self.__engine__)
        return Session()

    def create_ohlc_table(table_name: str, metadata) -> Table:
        return Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True, autoincrement="auto"),
            Column("datetime", DateTime, unique=True, nullable=False),
            Column("Date", Integer, index=True),
            Column("Product", String(20)),
            Column("TimeSn", Integer, index=True),
            Column("TimeSn_Dply", Integer),
            Column("Quantity", Integer),
            Column("Volume", Integer),
            Column("OPrice", Float),
            Column("HPrice", Float),
            Column("LPrice", Float),
            Column("CPrice", Float),
        )


class BaseSqlHandler:
    DB_NAME = None  # Override this

    def __init__(self):
        self.api_conn = None

    # Override this to generate the table for sqlalchemy
    def table_maker(self, table_name: str, metadata: MetaData) -> Table:
        pass

    # Override this to generate the table for sqlalchemy
    @property
    def get_data(self) -> callable:
        pass

    def insert(
        self,
        table_name: str,
        data,
        target: Literal["local", "remote", "all"],
        method: Literal["ignore", "replace"] = "ignore",
    ) -> None:
        if target == "all":
            target = ["local", "remote"]
        else:
            targets = [target]
        for target in targets:
            engine = self.engine_by_str(target)
            metadata = MetaData()
            table = self.table_maker(table_name, metadata)
            metadata.create_all(engine)
            with engine.connect() as conn:
                if engine.dialect.name == "mysql":
                    # pref_ = method
                    insert_stmt = mysql_insert(table).values(data)
                    stmt = insert_stmt.on_duplicate_key_update(
                        data=insert_stmt.inserted.items(), status="U"
                    )

                elif engine.dialect.name == "sqlite":
                    stmt = (
                        sqlite_insert(table)
                        .on_conflict_do_nothing(index_elements=[table.c.datetime])
                        .values(data)
                    )
                print(stmt)
                conn.execute(stmt)
                conn.commit()

    def get_latest_date(
        self, table_name: str, target: Literal["local", "remote", "all"]
    ) -> datetime | None:
        engine = self.engine_by_str(target)
        if not inspect(engine).has_table(table_name):
            return
        with engine.connect() as conn:
            metadata = MetaData()
            table = self.table_maker(table_name, metadata=metadata)
            stmt = Select(table.c.datetime).order_by(table.c.datetime.desc()).limit(1)
            dt = conn.execute(stmt).fetchone()
        if dt is None:
            logger.warning(f"No data found in {table_name}")
            return
        return dt.datetime


class TickHandler(BaseSqlHandler):
    DB_NAME = "mt_api_ta_tickdata"

    def table_maker(self, table_name: str, metadata: MetaData) -> Table:
        return Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True, autoincrement="auto"),
            Column("datetime", DateTime, nullable=False),
            Column("Prod", String(20)),
            Column("Sequence", Integer),
            Column("Match_Time", Float),
            Column("Match_Price", Float),
            Column("Match_Quantity", Integer),
            Column("Match_Volume", Integer),
            Column("Is_TryMatch", Boolean),
            Column("BS", Integer),
            Column("BP_1_Pre", Float),
            Column("SP_1_Pre", Float),
        )


def get_config_table(table_name: str = None, metadata: MetaData = None):
    metadata = MetaData(schema=settings.schemas.CONFIG)
    table_name = f"{root_settings.name}"
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("name", String, nullable=False),
        Column("key", String(20), nullable=False),
        Column("value", String, nullable=True),
        UniqueConstraint("name", "key", name="_name_key_uc"),
    )


@dataclass
class ConfigRow:
    name: str
    key: str
    value: str | None = None

    def dict(self):
        return {
            "name": self.name,
            "key": self.key,
            "value": self.value,
        }


get_config_table().metadata.create_all(bind=get_db()().bind)
