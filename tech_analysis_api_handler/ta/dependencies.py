from typing import Mapping
from fastapi import Depends, exceptions
from fastapi.security import OAuth2PasswordBearer
from tech_analysis_api_handler.database import get_db, get_config_table, ConfigRow
from tech_analysis_api_handler.config import get_settings
from tech_analysis_api_handler.models import (
    PostResponseModel,
    GetResponseModel,
    DeleteResponseModel,
    StatusCode,
    ResponseDataBase,
    DataType,
    RuntimeModel,
    StatusData,
    InfoData,
)

root_settings = get_settings()
settings = root_settings.modules_ta


async def valid_user_token(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/token")),
) -> dict:
    pass
    return {"user_id": "1111", "authorized": True}


async def valid_user(
    response: Mapping,
    token_data: dict = Depends(valid_user_token),
) -> Mapping:
    if token_data["authorized"] is not True:
        raise exceptions.RequestValidationError("Invalid authentication credentials.")
    return response


def ohlc_db():
    db = get_db()
    session = db()
    try:
        yield session
    finally:
        session.close()


def tick_db():
    db = get_db()
    session = db()
    try:
        yield session
    finally:
        session.close()
