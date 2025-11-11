from fastapi import FastAPI
from loguru import logger
import sys

from .router import router

app = FastAPI()

app.include_router(router, prefix="/v1/files")

logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    filter="obsidian-file-api",
    level="INFO",
)


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the File Listing API!",
    }
