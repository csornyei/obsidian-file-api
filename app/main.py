from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry import trace

from .config import config
from .logger import logger
from .router import router
from .telemetry import setup_tracing

tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info(
        "api_startup", environment=config.environment, log_level=config.log_level
    )
    yield
    logger.info("api_shutdown")


app = FastAPI(
    title="Obsidian File API",
    lifespan=lifespan,
)

setup_tracing(service_name="obsidian-file-api")

app.include_router(router, prefix="/v1/files")


@app.get("/")
async def read_root():
    with tracer.start_as_current_span("api.health_check"):
        logger.debug("health_check", status="ok")
        return {
            "message": "Welcome to the File Listing API!",
        }
