from enum import Enum
from typing import Any, List
from datetime import datetime
import asyncio
import pytz
import threading
from pydantic import BaseModel, Field, ConfigDict

from .utils import generate_systime


class ResponseModel(BaseModel):
    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
        populate_by_name=True,
    )

    def jsonify_response(self, **kwargs):
        """Return a dict which contains only serializable fields."""
        default_dict = self.model_dump_json()

        return default_dict


class StatusCode(BaseModel):
    class CodeBase(Enum):
        pass

    class Success(CodeBase):
        OK = 200
        CREATED = 201
        ACCEPTED = 202
        NO_CONTENT = 204

    class Redirection(CodeBase):
        NOT_MODIFIED = 304

    class ClientError(CodeBase):
        BAD_REQUEST = 400
        UNAUTHORIZED = 401
        FORBIDDEN = 403
        NOT_FOUND = 404
        METHOD_NOT_ALLOWED = 405
        CONFLICT = 409

    class ServerError(CodeBase):
        INTERNAL_SERVER_ERROR = 500
        NOT_IMPLEMENTED = 501
        BAD_GATEWAY = 502
        SERVICE_UNAVAILABLE = 503

    class RuntimeError(CodeBase):
        TASK_IS_RUNNING = 601
        TASK_NOT_FOUND = 602
        REQUEST_REJECTED = 603
        SYMBOL_ALREADY_SUBSCRIBED = 604
        SYMBOL_NOT_SUBSCRIBED = 605
        SERVICE_NOT_RUNNING = 606
        SERVICE_IS_RUNNING = 607


class RestfulResponseModel(ResponseModel):
    success: bool = Field(default=None, init=False)
    status_code: StatusCode.CodeBase
    status: str = Field(default=None, init=False)
    message: str = Field(default=None, init=False)
    error_message: str | None = None

    def model_post_init(self, __context: Any):
        self.status = self.status_code.name
        self.success = self.status_code.__class__ == StatusCode.Success


class DataType(Enum):
    STATUS = 1
    SYMBOLS = 2
    OHLC = 3
    TICK = 4
    INFO = 5


class ResponseDataBase(BaseModel):
    data_type: DataType
    id: int = Field(default=None, init=False)
    type: str = Field(default=None, init=False)
    systime: datetime = Field(default_factory=generate_systime, init=False)
    metadata: dict = Field(default_factory=dict, init=False)
    data: List = Field(default_factory=list, init=False)

    def model_post_init(self, __context: Any):
        self.id = self.data_type.value
        self.type = self.data_type.name
        self.systime = datetime.now(tz=pytz.timezone("Asia/Taipei"))


class MetaData(BaseModel):
    metadata: dict = Field(default_factory=dict, init=None)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        for k, v in kwargs.items():
            self.metadata[k] = v

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class GetResponseModel(RestfulResponseModel):
    data: List[ResponseDataBase] = Field(default_factory=list)


class PostResponseModel(RestfulResponseModel):
    pass


class DeleteResponseModel(RestfulResponseModel):
    pass


class RuntimeModel:

    def __init__(
        self,
        open_hour: datetime = None,
        close_hour: datetime = None,
        timezone: pytz = None,
        *args,
        **kwargs
    ):
        if not isinstance(open_hour, datetime) or not isinstance(close_hour, datetime):
            raise TypeError("open_hour and close_hour must be a datetime")
        self.__event__ = threading.Event()
        self.__thread__: threading.Thread = None
        self.__open_hour__ = open_hour
        self.__close_hour__ = close_hour
        self.__timezone__ = (
            pytz.timezone("Asia/Taipei") if timezone is None else timezone
        )
        self.__stop_signal__: bool = False

    def stop(self):
        if self.__thread__ is None or not self.__thread__.is_alive():
            return StatusCode.RuntimeError.SERVICE_NOT_RUNNING
        self.__event__.clear()
        self.__thread__.join()
        return StatusCode.Success.ACCEPTED

    def run(self) -> StatusCode:
        if self.__thread__ is not None and self.__thread__.is_alive():
            return StatusCode.RuntimeError.SERVICE_IS_RUNNING
        self.__event__.set()
        self.__thread__.start()
        return StatusCode.Success.ACCEPTED

    def set_task(self, task: callable = None):
        task = self.__task__ if task is None else task
        self.task = asyncio.create_task()
        self.__thread__ = threading.Thread(
            target=task,
        )

    def is_running(self) -> bool:
        if self.__thread__ is None:
            return False
        else:
            return self.__thread__.is_alive()

    def get_status(self) -> StatusCode:
        pass

    def check_time(self) -> bool:
        now = datetime.now(self.__timezone__).time()
        open = self.__open_hour__
        close = self.__close_hour__
        if open is not None and open > now:
            return False
        if close is not None and now > close:
            return False
        return True


class StatusData(ResponseDataBase):
    data_type: DataType = Field(default=DataType.STATUS, init=False)
    name: str = Field(default=None)
    active: bool = Field(default=None)
    status: str = Field(default=None)

    def model_post_init(self, __context: Any) -> None:

        self.metadata = {k: self[k] for k in ["name", "active", "status"]}
        super().model_post_init(__context)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class InfoData(ResponseDataBase):
    data_type: DataType = Field(default=DataType.INFO, init=False)
    name: str = Field(default=None)
    info: dict | None = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:

        self.metadata = {k: self[k] for k in ["name", "info"]}
        super().model_post_init(__context)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
