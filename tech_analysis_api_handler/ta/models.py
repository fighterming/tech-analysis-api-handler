from enum import Enum, auto
from .dependencies import StatusCode, RuntimeModel, StatusData


class Runtime(RuntimeModel):
    pass


class RtCode(Enum):
    SUCCESS = 1
    FAIL = 0
    DATA_ERROR = 2
    EMPTY_DATA = 3
    API_ERROR = 4
    DATABASE_ERROR = 5
    DUPLICATION_ERROR = 6


class Commands(Enum):
    LOGIN = auto()
    DISCONNECT = auto()


class k_setting:
    def __init__(self, ProdID, NK, TA_Type, DateBegin):
        self.ProdID = ProdID
        self.NK = NK
        self.TA_Type = TA_Type
        self.DateBegin = DateBegin
