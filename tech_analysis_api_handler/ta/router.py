from fastapi import APIRouter, BackgroundTasks, Depends
from contextlib import asynccontextmanager
from .schemas import TAResponse
from . import service
from .dependencies import (
    ohlc_db,
    tick_db,
    settings,
    StatusCode,
)
from .schemas import GetResponse, PostResponse, PutResponse, DeleteResponse


def init():
    service.connect()
    service.post_init()


def get_router() -> APIRouter:
    ep = settings.endpoints

    router = APIRouter()

    @router.get(ep.SNAPSHOT, response_model=GetResponse)
    def snapshot():
        return GetResponse(status_code=StatusCode.Success.OK)

    @router.post(ep.SERVICE, response_model=PostResponse)
    async def connect():
        return await service.connect()

    @router.put(ep.SUBSCRIPTION + "/{symbol}", response_model=PutResponse)
    async def subscribe(symbol: str):
        return await service.subscribe(symbol)

    @router.delete(ep.SUBSCRIPTION + "/{symbol}", response_model=DeleteResponse)
    async def unsubscribe(symbol: str):
        return await service.unsubscribe(symbol)

    @router.get(ep.SUBSCRIPTIONS, response_model=GetResponse)
    async def list_subscriptions():
        return await service.list_subscriptions()

    @router.put(ep.OHLC + "/{symbol}", response_model=PutResponse)
    async def ohlc_update(symbol: str, db=Depends(ohlc_db)):
        return await service.ohlc_update(db, symbol)

    @router.get(ep.OHLC + ep.SERVICE, response_model=GetResponse)
    async def get_ohlc_status():
        return service.get_ohlc_status()

    @router.post(ep.OHLC + ep.SERVICE, response_model=PostResponse)
    async def start_ohlc_update():
        return service.start_ohlc_update()

    @router.delete(ep.OHLC + ep.SERVICE, response_model=DeleteResponse)
    async def stop_ohlc_update():
        return service.stop_ohlc_update()

    @router.get(ep.TICK + ep.SERVICE, response_model=GetResponse)
    async def get_tick_status():
        return service.get_tick_status()

    @router.post(ep.TICK + ep.SERVICE, response_model=PostResponse)
    async def start_tick_update():
        return service.get_tick_status()

    @router.delete(ep.TICK + ep.SERVICE, response_model=DeleteResponse)
    async def stop_tick_update():
        return service.get_tick_status()

    @router.get(ep.INFO, response_model=GetResponse)
    async def load():
        return service.load()

    @router.put(ep.INFO, response_model=PutResponse)
    async def save():
        return service.save()

    ################################################################

    @router.get("/unsuball/", response_model=TAResponse)
    async def unsubscribe_all():
        response_result = await service.unsubscribe_all()
        return response_result

    @router.get("/ohlc/fetch/{symbol}", response_model=TAResponse)
    def fetch(symbol: str, db=Depends(ohlc_db)):
        response_result = service.fetch(db, symbol)
        return response_result

    return router


router = get_router()
