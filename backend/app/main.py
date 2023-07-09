import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from logging.config import dictConfig
import logging

# from motor.motor_asyncio import AsyncIOMotorClient

from routers.matchdetails import router as matchdetails_router
from routers.matches import router as matches_router
from routers.predictors import model_router as predictors_router
from config import settings

# from utils.parse_config import ConfigParser

from dependencies import mongodb_client, database

from config import LogConfig, get_settings

dictConfig(LogConfig().dict())
logger = logging.getLogger("app")

origins: list[str] = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://0.0.0.0",
    "http://0.0.0.0:3000",
]

app: FastAPI = FastAPI(title=get_settings().app_name)
args = None
options = None
config = None


@app.on_event("startup")
async def startup_db_client() -> None:
    app.mongodb_client = mongodb_client  # AsyncIOMotorClient(settings.db_uri)
    app.mongodb_client.get_io_loop = asyncio.get_running_loop
    app.database = database  # app.mongodb_client[settings.db_name]


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    app.mongodb_client.close()


# Middleware
app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(matchdetails_router, tags=["matchdetails"], prefix="/matchdetail")
app.include_router(matches_router, tags=["matches"], prefix="/match")
app.include_router(predictors_router, tags=["predictors"])


async def main() -> None:

    config: uvicorn.Config = uvicorn.Config(
        "main:app",
        host=settings.HOST,
        reload=settings.DEBUG_MODE,
        port=settings.PORT,
    )

    server: uvicorn.Server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
