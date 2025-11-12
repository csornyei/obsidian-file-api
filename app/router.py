from typing import Literal, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from loguru import logger

from .file_handler import FileHandler, get_file_handler
from .exception import CustomError


class FileContent(BaseModel):
    frontmatter: Optional[dict]
    content: Optional[list[str]]


router = APIRouter()


@router.get("/")
async def list_files(
    resp: Response,
    path: str = "",
    type: Literal["files", "files_all", "dirs", "dirs_all"] = "files_all",
    fh: FileHandler = Depends(get_file_handler),
):
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
        return files
    except CustomError as ce:
        logger.error(f"CustomError in list_files: {ce.message}")
        resp.status_code = ce.status_code
        return ce.to_response()
    except Exception as e:
        logger.error(f"Unexpected error in list_files: {e}")
        resp.status_code = 500
        return {"error": "An unexpected error occurred."}


@router.get("/read")
async def read_file(
    response: Response,
    path: str,
    content: Literal["full", "frontmatter", "text"] = "full",
    fh: FileHandler = Depends(get_file_handler),
):
    try:
        match content:
            case "text":
                file_content = fh.get_text_content(path)
                return {"content": file_content}
            case "full":
                file_content = fh.read_file(path)
                return {"content": file_content}
            case "frontmatter":
                frontmatter = fh.get_frontmatter(path)
                return {"frontmatter": frontmatter}

    except CustomError as ce:
        response.status_code = ce.status_code
        logger.error(f"CustomError in read_file: {ce.message}")
        return ce.to_response()
    except Exception as e:
        response.status_code = 500
        logger.error(f"Unexpected error in read_file: {e}")
        return {"error": "An unexpected error occurred."}


@router.post("/write", status_code=201)
async def write_file(
    response: Response,
    path: str,
    content: FileContent,
    fh: FileHandler = Depends(get_file_handler),
):
    try:
        fh.write_file(path, content.frontmatter, content.content)
        return {"status": "success"}
    except CustomError as ce:
        response.status_code = ce.status_code
        logger.error(f"CustomError in write_file: {ce.message}")
        return ce.to_response()
    except Exception as e:
        response.status_code = 500
        logger.error(f"Unexpected error in write_file: {e}")
        return {"error": "An unexpected error occurred."}


@router.patch("/write", status_code=204)
async def update_file(
    response: Response,
    path: str,
    type: Literal["frontmatter", "content"],
    content: FileContent,
    fh: FileHandler = Depends(get_file_handler),
):
    logger.info(f"Updating file at path: {path} with type: {type}")
    try:
        match type:
            case "frontmatter":
                fh.update_frontmatter(path, content.frontmatter)
            case "content":
                fh.update_content(path, content.content)

        return {"status": "success"}
    except CustomError as ce:
        logger.error(f"CustomError in update_file: {ce.message}")
        response.status_code = ce.status_code
        return ce.to_response()
    except Exception as e:
        logger.error(f"Unexpected error in update_file: {e}")
        response.status_code = 500
        return {"error": "An unexpected error occurred."}
