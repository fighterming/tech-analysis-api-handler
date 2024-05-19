import multiprocessing
import threading
import queue
import logging
import asyncio
from typing import Literal
import time
import pandas as pd
from datetime import datetime
import pytz
from dataclasses import dataclass, field
from typing import Literal

from tech_analysis_api_v2.api import TechAnalysis, TechAnalysisAPI, timedelta
from tech_analysis_api_v2.model import eTA_Type, TBSRec, eNK_Kind
from tech_analysis_api_handler.database import (
    TickHandler,
)

from twse_codes import codes
from .models import RtCode, StatusCode, Runtime
from .schemas import (
    TAResponse,
    GetResponse,
    PostResponse,
    PutResponse,
    DeleteResponse,
    SymbolsData,
    OHLCData,
    TickData,
    StatusData,
    InfoData,
)
from .utils import is_today, today, combine_date_time, today, kbar_time_formatter
from .dependencies import settings, root_settings, get_config_table, get_db, ConfigRow
from tech_analysis_api_handler.database import (
    Session,
    table_exist,
    OHLCTable,
    get_latest_datetime,
    MetaData,
    sqlite_insert,
    select,
)
from .dependencies import get_db
from sqlalchemy.orm import mapper

logger = logging.getLogger("runtime")
event = threading.Event()


def post_init():
    __ohlc_runtime.__load__()


class OHLCRuntime:
    @dataclass
    class Config:
        name: str = ""
        is_active: bool = False
        updating_symbol: str | None = None

        def __post_init__(self):
            if self.is_active in ["true", "false"]:
                self.is_active = True if self.is_active == "true" else False

        def to_sql(self) -> list[dict]:
            name = self.name
            return [
                {"name": name, "key": k, "value": v}
                for k, v in self.__dict__.items()
                if k != "name"
            ]

        @classmethod
        def from_sql(cls, data: list[dict]):
            return cls(**{k: v for k, v in data})

    @property
    def config(self) -> Config:
        return self.__config__

    def __init__(
        self,
        name: str = "OHLCRuntime",
        open_hour: datetime = None,
        close_hour: datetime = None,
        timezone: pytz = None,
        *args,
        **kwargs,
    ):
        if open_hour is not None and not isinstance(open_hour, datetime):
            raise TypeError("open_hour and close_hour must be a datetime")
        if close_hour is not None and not isinstance(close_hour, datetime):
            raise TypeError("close and close_hour must be a datetime")
        self.__name__ = f"{__name__}.{self.__class__.__name__}"
        self.__event__ = threading.Event()
        self.__open_hour__ = open_hour
        self.__close_hour__ = close_hour
        self.__timezone__ = (
            pytz.timezone("Asia/Taipei") if timezone is None else timezone
        )
        self.__stop_signal__: bool = False
        self.__config__ = self.Config(name=f"{__name__}.{__class__.__name__}")
        self.thread: threading.Thread = None

    def __save__(self):
        table = get_config_table()
        db = get_db()
        with db() as session:

            stmt = sqlite_insert(table).values(self.config.to_sql())
            stmt = stmt.on_conflict_do_update(
                constraint="_name_key_uc",
                set_={"value": stmt.excluded.value},
            )
            session.execute(stmt)
            session.commit()

    def __load__(self) -> None:
        table = get_config_table()
        db = get_db()
        with db() as session:
            stmt = select(table.c.key, table.c.value).where(
                table.c.name == self.__name__
            )
            cfg = session.execute(stmt).all()
        self.__config__.__dict__.update({k: v for k, v in cfg})

        if self.config.is_active:
            self.run()

    def stop(self):
        if self.thread is None or not self.thread.is_alive():
            return StatusCode.RuntimeError.SERVICE_NOT_RUNNING
        self.__event__.clear()
        self.thread.join()
        self.__save__()
        return StatusCode.Success.ACCEPTED

    def run(self) -> StatusCode:
        if self.thread is not None and self.thread.is_alive():
            return StatusCode.RuntimeError.SERVICE_IS_RUNNING
        self.__event__.set()
        self.thread = threading.Thread(target=self.task)
        self.thread.start()
        return StatusCode.Success.OK

    # TODO
    def task(self) -> None:
        limit = 10
        count = 0
        while True:
            if ApiConnector is not None and ApiConnector.api is not None:
                break
            count += 1
            time.sleep(1)
            if count == limit:
                return

        symbols = codes.get_stocks_list()
        latest_dt = today() - settings.STARTDATE_OFFSET
        latest_dt = latest_dt.strftime("%Y%m%d")
        symbols_ = (
            symbols[symbols.index(self.config.updating_symbol) :]
            if self.config.updating_symbol
            else symbols
        )
        for symbol in symbols_:
            self.__config__.updating_symbol = symbol
            self.__config__.is_active = True
            self.__save__()
            k_config = ApiConnector.api.get_k_setting(
                product=symbol,
                ta_type=eTA_Type.SMA,
                nk_Kind=eNK_Kind.K_1m,
                date=latest_dt,
            )
            print(latest_dt, symbol)
            ApiConnector.api.SubTA(k_config)
            while DataQueue.async_queue.empty():
                if not self.__event__.is_set():
                    return
                time.sleep(0.1)
            DataQueue.async_queue.get()
            if self.config.updating_symbol == symbols[-1]:
                self.config.updating_symbol = None
            ApiConnector.api.UnSubTA(k_config)

        return

    def is_running(self) -> bool:
        if self.thread is None:
            return False
        else:
            return self.thread.is_alive()

    def get_status(self) -> Config:
        is_running = self.is_running
        if is_running:
            status = f"Updating: {self.config.updating_symbol}"
        else:
            status = "Stopped."
        return StatusData(name=__name__, active=self.is_running(), status=status)

    def check_time(self) -> bool:
        now = datetime.now(self.__timezone__).time()
        open = self.__open_hour__
        close = self.__close_hour__
        if open is not None and open > now:
            return False
        if close is not None and now > close:
            return False
        return True


__ohlc_runtime = OHLCRuntime()


def get_ohlc_instance() -> OHLCRuntime:
    return __ohlc_runtime


class TickRuntime:

    def __init__(
        self,
        name: str = "TickRuntime",
        open_hour: datetime = None,
        close_hour: datetime = None,
        timezone: pytz = None,
        *args,
        **kwargs,
    ):
        if open_hour is not None and not isinstance(open_hour, datetime):
            raise TypeError("open_hour and close_hour must be a datetime")
        if close_hour is not None and not isinstance(close_hour, datetime):
            raise TypeError("close and close_hour must be a datetime")
        self.__name__ = name
        self.__event__ = threading.Event()
        self.__open_hour__ = open_hour
        self.__close_hour__ = close_hour
        self.__timezone__ = (
            pytz.timezone("Asia/Taipei") if timezone is None else timezone
        )
        self.__stop_signal__: bool = False
        self.thread: threading.Thread = None

    def stop(self):
        if self.thread is None or not self.thread.is_alive():
            return StatusCode.RuntimeError.SERVICE_NOT_RUNNING
        self.__event__.clear()
        self.thread.join()
        return StatusCode.Success.ACCEPTED

    def run(self) -> StatusCode:
        if self.thread is not None and self.thread.is_alive():
            return StatusCode.RuntimeError.SERVICE_IS_RUNNING
        self.__event__.set()
        self.thread = threading.Thread(target=self.task)
        self.thread.start()
        return StatusCode.Success.OK

    def task(self) -> None:

        end_date = datetime.now(pytz.timezone("Asia/Taipei")).replace(tzinfo=None)
        start_date = (end_date - pd.DateOffset(weeks=1)).replace(tzinfo=None)
        all_data = []
        symbols = codes.get_stocks_list()
        for symbol in symbols:
            for single_date in pd.date_range(
                start=start_date, end=end_date.replace(tzinfo=None)
            ):
                lsBS, sErrMsg = ApiConnector.api.GetHisBS_Stock(symbol, single_date)
                if sErrMsg:
                    if sErrMsg == RtCode.DATA_ERROR:
                        logger.warning("%s is up to date", symbol)
                    else:
                        logger.warning(sErrMsg)
                else:
                    data = [
                        x.__dict__.update(
                            {"datetime": combine_date_time(x.Match_Time, single_date)}
                        )
                        for x in lsBS
                    ]
            print(data)

    def is_running(self) -> bool:
        if self.thread is None:
            return False
        else:
            return self.thread.is_alive()

    def get_status(self) -> StatusData:
        is_running = self.is_running
        if is_running:
            status = f"Updating: {self.config.updating_symbol}"
        else:
            status = "Stopped."
        return StatusData(name=__name__, active=self.is_running(), status=status)

    def check_time(self) -> bool:
        now = datetime.now(self.__timezone__).time()
        open = self.__open_hour__
        close = self.__close_hour__
        if open is not None and open > now:
            return False
        if close is not None and now > close:
            return False
        return True


__tick_runtime = TickRuntime()

### Router interface main functions


def connect():
    r = ApiResponse
    api = CustomTechAnalysis(
        r.OnDigitalSSOEvent, r.OnTAConnStuEvent, r.OnUpdate, r.OnRcvDone
    )
    username = settings.secrets.USERNAME
    password = settings.secrets.PASSWORD
    api.Login(username, password)
    result = event.wait()
    if result:
        ApiConnector.set_api(api)
        return PostResponse(status_code=StatusCode.Success.OK)
    else:
        return PostResponse(status_code=StatusCode.RuntimeError.REQUEST_REJECTED)


async def subscribe(product_id: str):
    today = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
    k_config = ApiConnector.api.get_k_setting(
        product_id, ta_type=eTA_Type.SMA, nk_Kind=eNK_Kind.K_1m, date=today
    )
    api = ApiConnector.api
    for setting in api.Subscribed_Symbol:
        if setting.ProdID == k_config.ProdID:
            return PutResponse(
                status_code=StatusCode.RuntimeError.SYMBOL_ALREADY_SUBSCRIBED
            )
    api.SubTA(k_config)
    api.Subscribed_Symbol.append(k_config)

    return PutResponse(status_code=StatusCode.Success.ACCEPTED)


async def unsubscribe(product_id: str):
    today = today(format="%Y%m%d")
    k_config = ApiConnector.api.get_k_setting(
        product_id, ta_type=eTA_Type.SMA, nk_Kind=eNK_Kind.K_1m, date=today
    )
    if k_config not in ApiConnector.api.Subscribed_Symbol:
        return DeleteResponse(status_code=StatusCode.RuntimeError.SYMBOL_NOT_SUBSCRIBED)

    ApiConnector.api.UnSubTA(k_config)
    return DeleteResponse(status_code=StatusCode.Success.ACCEPTED)


async def list_subscriptions():
    data = []
    for k_config in ApiConnector.api.Subscribed_Symbol:
        data.append(k_config.ProdID)

    return GetResponse(status_code=StatusCode.Success.OK, data=[SymbolsData(data=data)])


# TODO: No dict return from api for now
async def ohlc_get(symbol: str):
    latest_dt = today(format="%Y%m%d")
    k_config = ApiConnector.api.get_k_setting(
        product=symbol, ta_type=eTA_Type.SMA, nk_Kind=eNK_Kind.K_1m, date=latest_dt
    )
    while True:
        ApiConnector.api.SubTA(k_config)
        data = await DataQueue.async_queue.get()
        ApiConnector.api.UnSubTA(k_config)
        break

    return GetResponse(status_code=StatusCode.Success.OK, data=[OHLCData(data=data)])


async def ohlc_update(db: Session, symbol: str):
    latest_dt = today() - settings.STARTDATE_OFFSET
    while False:
        if table_exist(db, symbol):
            latest_dt = today() - settings.STARTDATE_OFFSET
        else:
            latest_dt = get_latest_datetime(db, table)
    latest_dt = latest_dt.strftime("%Y%m%d")
    k_config = ApiConnector.api.get_k_setting(
        product=symbol, ta_type=eTA_Type.SMA, nk_Kind=eNK_Kind.K_1m, date=latest_dt
    )
    while True:
        ApiConnector.api.SubTA(k_config)
        data = await DataQueue.async_queue.get()
        ApiConnector.api.UnSubTA(k_config)
        break

    return PutResponse(status_code=StatusCode.Success.OK)


def load():
    info = __ohlc_runtime.__load__().__dict__
    name = info.pop("name", __name__)
    data = [InfoData(name=name, info=info)]
    return GetResponse(status_code=StatusCode.Success.OK, data=data)


def save():
    info = __ohlc_runtime.__save__()
    return PutResponse(status_code=StatusCode.Success.ACCEPTED)


def start_ohlc_update():
    result = __ohlc_runtime.run()
    return PostResponse(status_code=result)


def stop_ohlc_update():
    result = __ohlc_runtime.stop()
    return DeleteResponse(status_code=result)


def get_ohlc_status():
    data = __ohlc_runtime.get_status()
    return GetResponse(status_code=StatusCode.Success.OK, data=[data])


def start_tick_update():
    result = __ohlc_runtime.run()
    return PostResponse(status_code=result)


def stop_tick_update():
    print("stopping ohlc runtime...")
    result = __ohlc_runtime.stop()
    return DeleteResponse(status_code=result)


def get_tick_status():
    data = __ohlc_runtime.get_status()
    return GetResponse(status_code=StatusCode.Success.OK, data=[data])


async def subscribe_all():
    today = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
    symbols = sorted(codes.get_stocks_list())
    for symbol in symbols:
        k_config = ApiConnector.api.get_k_setting(
            symbol, ta_type=eTA_Type.SMA, nk_Kind=eNK_Kind.K_1m, date=today
        )
        api = ApiConnector.api
        for setting in api.Subscribed_Symbol:
            if setting.ProdID == k_config.ProdID:
                continue
        api.SubTA(k_config)
        api.Subscribed_Symbol.append(k_config)

    return TAResponse(success=True, status_code=RtCode.SUCCESS, data=symbols)


async def unsubscribe_all():
    today = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
    for k_config in ApiConnector.api.Subscribed_Symbol:
        ApiConnector.api.UnSubTA(k_config)
    return TAResponse(success=True, status_code=RtCode.SUCCESS)


class DataQueue:
    data_queue = queue.Queue()
    async_queue = asyncio.Queue()


def get_historical_data(
    product_id: str, start_date: datetime = None, end_date: datetime = None
) -> list | None:
    if end_date is None:
        end_date = datetime.now(pytz.timezone("Asia/Taipei")).replace(tzinfo=None)
    if start_date is None:
        start_date = (end_date - pd.DateOffset(weeks=1)).replace(tzinfo=None)

    if is_today(start_date):
        return RtCode.DATA_ERROR
    all_data = []
    for single_date in pd.date_range(
        start=start_date, end=end_date.replace(tzinfo=None)
    ):
        lsBS, sErrMsg = ApiConnector.api.GetHisBS_Stock(product_id, single_date)
        if sErrMsg:
            if sErrMsg == RtCode.DATA_ERROR:
                logger.info("%s is up to date", product_id)
            else:
                logger.warning(sErrMsg)
        else:
            for x in lsBS:
                data_point = x.__dict__
                data_point.update(
                    {"datetime": combine_date_time(x.Match_Time, single_date)}
                )
                all_data.append(data_point)
    return all_data


def update_tickdata(target: Literal["local", "remote", "all"]):
    handler = TickHandler()
    ac = ApiConnector()
    ac.connect()
    for code in codes.get_stocks_list():
        dt = handler.get_latest_date(code, target)
        start_date = dt + timedelta(days=1) if dt is not None else None
        data = ac.get_historical_data(code, start_date)
        if data == RtCode.DATA_ERROR:
            continue
        if data == RtCode.EMPTY_DATA:
            continue
        elif data == None or len(data) == 0:
            logger.warning("Data not available from api for %s", code)
            continue
        handler.insert(code, data, target)


class ApiResponse:
    ohlc_db = get_db()

    def OnDigitalSSOEvent(aIsOK, aMsg):
        print(f"OnDigitalSSOEvent: {aIsOK} {aMsg}")

    def OnTAConnStuEvent(aIsOK):
        print(f"OnTAConnStuEvent: {aIsOK}")
        if aIsOK:
            event.set()
        else:
            event.clear()

    def OnUpdate(ta_Type: eTA_Type, aResultPre, aResultLast):

        print(f"OnUpdate: {aResultPre}")
        args = {"result": aResultLast}
        threading.Thread(
            target=ApiResponse.thread_onupdate,
            args=(
                ta_Type,
                aResultPre,
                aResultLast,
            ),
        ).start()
        pass

    def OnRcvDone(ta_Type: eTA_Type, aResult):
        symbol = aResult[0].KBar.Product
        print(f"OnRcvDone: {symbol}")
        event.set()
        thread = threading.Thread(
            target=ApiResponse.thread_onrcvdone, args=(aResult,)
        ).start()

    @classmethod
    def thread_onupdate(cls, ta_Type: eTA_Type, aResultPre, aResultLast):
        db = get_db()
        with db() as session:
            aResultPre = [kbar_time_formatter(aResultPre)]
            OHLCTable.insert_ignore(db=session, data=aResultPre)

    @classmethod
    def thread_onrcvdone(cls, result):
        dataset = [kbar_time_formatter(r) for r in result]
        db = get_db()
        try:
            with db() as session:

                OHLCTable.insert_ignore(db=session, data=dataset)
        except Exception as e:
            logger.error(e)
            if get_ohlc_instance().is_running():
                DataQueue.async_queue.put_nowait(RtCode.DATA_ERROR)
        else:
            if get_ohlc_instance().is_running():
                DataQueue.async_queue.put_nowait(RtCode.SUCCESS)
        return


class CustomTechAnalysis(TechAnalysis):
    Subscribed_Symbol = []

    def GetHisBS_Stock(self, ProdID, Date: datetime):
        tSubBSRec = TechAnalysisAPI.TSubBSRec()
        tSubBSRec.ProdID = ProdID
        tSubBSRec.Date = Date.strftime("%Y%m%d")
        flag, lsBS, aErrMsg = self.fTechAnalysisAPI.GetHisBS_Stock(tSubBSRec, None, "")
        if flag:
            lsbss = []
            for x in lsBS:
                tk_bar_rec = TBSRec(
                    x.Prod,
                    x.Sequence,
                    float(str(x.Match_Time)),
                    float(str(x.Match_Price)),
                    x.Match_Quantity,
                    x.Match_Volume,
                    x.Is_TryMatch,
                    x.BS,
                    float(str(x.BP_1_Pre)),
                    float(str(x.SP_1_Pre)),
                )
                lsbss.append(tk_bar_rec)
            return lsbss, aErrMsg
        else:
            if is_today(Date):
                return None, RtCode.DATA_ERROR
            else:
                return None, RtCode.API_ERROR

    def get_ohlc(self, ProdID, start_date: str | datetime, period: eNK_Kind):
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y%m%d")
        k_config = TechAnalysis.get_k_setting(ProdID, eTA_Type.SMA, period, start_date)
        self.SubTA(k_config)


class ApiConnector:
    api: CustomTechAnalysis = None

    @classmethod
    def set_api(cls, api: CustomTechAnalysis):
        cls.api = api
        print("api set")

    @classmethod
    def get_api(cls) -> CustomTechAnalysis:
        return cls.api
