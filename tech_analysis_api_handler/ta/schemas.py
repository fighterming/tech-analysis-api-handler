from datetime import datetime
from tech_analysis_api_v2.model import eTA_Type, TBSRec, eNK_Kind
from typing import Optional, Literal, List

from pydantic import BaseModel, Field

from .dependencies import (
    GetResponseModel,
    PostResponseModel,
    ResponseDataBase,
    DataType,
    StatusData,
    InfoData,
)


class GetResponse(GetResponseModel):
    pass


class PostResponse(PostResponseModel):
    pass


class PutResponse(PostResponseModel):
    pass


class DeleteResponse(PostResponseModel):
    pass


class SymbolsData(ResponseDataBase):
    data_type: DataType = Field(default=DataType.SYMBOLS, init=False)
    data: List[str]


class OHLCData(ResponseDataBase):
    data_type: DataType = Field(default=DataType.OHLC, init=False)
    data: dict = Field(default_factory=dict)


class TickData(ResponseDataBase):
    data_type: DataType = Field(default=DataType.TICK, init=False)
    data: dict = Field(default_factory=dict)


class TAResponse(BaseModel):
    success: bool
    status_code: int
    message: str | None = None
    data: list | None = None
    error_code: int | None = None
    error_message: str | None = None


class OHLC(BaseModel):
    id: int
    datetime: datetime
