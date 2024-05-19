import subprocess
import sys
import os
import threading
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from tech_analysis_api_handler.ta import router


from tech_analysis_api_handler.ta import service

from .models import GetResponseModel, StatusCode, PostResponseModel
from . import config


def init():
    router.init()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init()
        yield

    settings = config.get_settings()
    app = FastAPI(lifespan=lifespan)
    print("FastAPI started running..")

    ep = settings.endpoints

    @app.get(ep.SNAPSHOT)
    def index():
        return GetResponseModel(status_code=StatusCode.Success.OK)

    @app.post(ep.SHUTDOWN)
    def shutdown():
        # Spawn a new process to run the script
        os._exit(0)

    @app.post(ep.RESTART)
    def restart():
        print(ep.RESTART)

        def _restart():
            python = sys.executable
            subprocess.Popen([python, sys.argv[0]])
            os._exit(0)

        event = threading.Thread(target=_restart)
        event.start()
        return PostResponseModel(status_code=StatusCode.Success.OK)

    app.include_router(router.router, prefix=settings.modules_ta.PREFIX)

    return app


app = create_app()
