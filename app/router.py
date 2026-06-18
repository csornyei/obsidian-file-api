import time
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Response
from opentelemetry import trace
from pydantic import BaseModel, field_validator

from .exception import CustomError
from .file_handler import FileHandler, get_file_handler
from .logger import logger

tracer = trace.get_tracer(__name__)


class FileContent(BaseModel):
    frontmatter: Optional[dict] = None
    content: Optional[list[str]] = None

    @field_validator("frontmatter", "content", mode="before")
    @classmethod
    def validate_at_least_one(cls, v: any) -> any:
        return v

    def __init__(self, **data):
        super().__init__(**data)
        if self.frontmatter is None and self.content is None:
            raise ValueError("Either frontmatter or content must be provided")


router = APIRouter()


@router.get("/")
async def list_files(
    resp: Response,
    path: str = "",
    type: Literal["files", "files_all", "dirs", "dirs_all"] = "files_all",
    fh: FileHandler = Depends(get_file_handler),
):
    start_time = time.perf_counter()
    with tracer.start_as_current_span("file.list") as span:
        span.set_attribute("path", path)
        span.set_attribute("list.type", type)

        try:
            match type:
                case "dirs":
                    files = fh.list_dirs(path)
                case "dirs_all":
                    files = fh.list_dirs(path, all=True)
                case "files":
                    files = fh.list_files(path)
                case "files_all":
                    files = fh.list_files(path, all=True)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("result.count", len(files))
            span.set_attribute("result.latency_ms", elapsed_ms)

            logger.info(
                "file_list_success",
                path=path,
                list_type=type,
                result_count=len(files),
                latency_ms=elapsed_ms,
            )

            return files

        except CustomError as ce:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", ce.status_code)
            span.set_attribute("error.type", "validation_error")
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.warning(
                "file_list_validation_error",
                path=path,
                list_type=type,
                status_code=ce.status_code,
                message=ce.message,
                latency_ms=elapsed_ms,
            )
            resp.status_code = ce.status_code
            return ce.to_response()

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", 500)
            span.set_attribute("error.type", "unexpected")
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.error(
                "file_list_error",
                path=path,
                list_type=type,
                error=str(e),
                latency_ms=elapsed_ms,
                exc_info=True,
            )
            resp.status_code = 500
            return {"error": "An unexpected error occurred."}


@router.get("/read")
async def read_file(
    response: Response,
    path: str,
    content: Literal["full", "frontmatter", "text"] = "full",
    fh: FileHandler = Depends(get_file_handler),
):
    start_time = time.perf_counter()
    with tracer.start_as_current_span("file.read") as span:
        span.set_attribute("path", path)
        span.set_attribute("read.type", content)

        try:
            match content:
                case "text":
                    file_content = fh.get_text_content(path)
                    content_lines = len(file_content)
                    result = {"content": file_content}

                case "full":
                    file_content = fh.read_file(path)
                    content_lines = len(file_content)
                    result = {"content": file_content}

                case "frontmatter":
                    file_content = fh.get_frontmatter(path)
                    content_lines = 0
                    result = {"frontmatter": file_content}

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("result.lines", content_lines)
            span.set_attribute("result.latency_ms", elapsed_ms)

            logger.info(
                "file_read_success",
                path=path,
                read_type=content,
                result_lines=content_lines,
                latency_ms=elapsed_ms,
            )

            return result

        except CustomError as ce:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", ce.status_code)
            span.set_attribute("error.type", "validation_error")
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.warning(
                "file_read_validation_error",
                path=path,
                read_type=content,
                status_code=ce.status_code,
                message=ce.message,
                latency_ms=elapsed_ms,
            )
            response.status_code = ce.status_code
            return ce.to_response()

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", 500)
            span.set_attribute("error.type", "unexpected")
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.error(
                "file_read_error",
                path=path,
                read_type=content,
                error=str(e),
                latency_ms=elapsed_ms,
                exc_info=True,
            )
            response.status_code = 500
            return {"error": "An unexpected error occurred."}


@router.post("/write", status_code=201)
async def write_file(
    response: Response,
    path: str,
    content: FileContent,
    fh: FileHandler = Depends(get_file_handler),
):
    start_time = time.perf_counter()
    with tracer.start_as_current_span("file.write") as span:
        span.set_attribute("path", path)

        try:
            fm_size = len(str(content.frontmatter)) if content.frontmatter else 0
            content_size = (
                sum(len(line) for line in content.content) if content.content else 0
            )
            total_size = fm_size + content_size

            fh.write_file(path, content.frontmatter, content.content)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("write.frontmatter_size", fm_size)
            span.set_attribute("write.content_size", content_size)
            span.set_attribute("write.total_size", total_size)
            span.set_attribute("write.content_lines", len(content.content or []))
            span.set_attribute("result.latency_ms", elapsed_ms)

            logger.info(
                "file_write_success",
                path=path,
                frontmatter_size=fm_size,
                content_size=content_size,
                total_size=total_size,
                content_lines=len(content.content or []),
                latency_ms=elapsed_ms,
            )

            return {"status": "success"}

        except CustomError as ce:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", ce.status_code)
            span.set_attribute("error.type", "validation_error")
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.warning(
                "file_write_validation_error",
                path=path,
                status_code=ce.status_code,
                message=ce.message,
                latency_ms=elapsed_ms,
            )
            response.status_code = ce.status_code
            return ce.to_response()

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", 500)
            span.set_attribute("error.type", "unexpected")
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.error(
                "file_write_error",
                path=path,
                error=str(e),
                latency_ms=elapsed_ms,
                exc_info=True,
            )
            response.status_code = 500
            return {"error": "An unexpected error occurred."}


@router.patch("/write", status_code=204)
async def update_file(
    response: Response,
    path: str,
    type: Literal["frontmatter", "content"],
    content: FileContent,
    fh: FileHandler = Depends(get_file_handler),
):
    start_time = time.perf_counter()
    with tracer.start_as_current_span("file.update") as span:
        span.set_attribute("path", path)
        span.set_attribute("update.type", type)

        try:
            match type:
                case "frontmatter":
                    fm_size = (
                        len(str(content.frontmatter)) if content.frontmatter else 0
                    )
                    fh.update_frontmatter(path, content.frontmatter)
                    update_size = fm_size

                case "content":
                    content_size = (
                        sum(len(line) for line in content.content)
                        if content.content
                        else 0
                    )
                    logger.info(content.content)
                    fh.update_content(path, content.content)
                    update_size = content_size

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("update.size", update_size)
            span.set_attribute(
                "update.lines", len(content.content or []) if type == "content" else 0
            )
            span.set_attribute("result.latency_ms", elapsed_ms)

            logger.info(
                "file_update_success",
                path=path,
                update_type=type,
                update_size=update_size,
                update_lines=len(content.content or []) if type == "content" else 0,
                latency_ms=elapsed_ms,
            )

            return {"status": "success"}

        except CustomError as ce:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", ce.status_code)
            span.set_attribute("error.type", "validation_error")
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.warning(
                "file_update_validation_error",
                path=path,
                update_type=type,
                status_code=ce.status_code,
                message=ce.message,
                latency_ms=elapsed_ms,
            )
            response.status_code = ce.status_code
            return ce.to_response()

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("error.status_code", 500)
            span.set_attribute("error.type", "unexpected")
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.latency_ms", elapsed_ms)

            logger.error(
                "file_update_error",
                path=path,
                update_type=type,
                error=str(e),
                latency_ms=elapsed_ms,
                exc_info=True,
            )
            response.status_code = 500
            return {"error": "An unexpected error occurred."}
