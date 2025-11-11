from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

from .env import BASE_DIR
from .file_handler import FileHandler


class FileContent(BaseModel):
    frontmatter: Optional[dict]
    content: Optional[list[str]]


router = APIRouter()

fh = FileHandler(base_folder=BASE_DIR)


@router.get("/")
async def list_files(
    path: str = "",
    type: Literal["files", "files_all", "dirs", "dirs_all"] = "files_all",
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
    except ValueError as e:
        return {"error": str(e)}


@router.get("/read")
async def read_file(
    path: str, content: Literal["full", "frontmatter", "text"] = "full"
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

    except ValueError as e:
        return {"error": str(e)}


@router.post("/write")
async def write_file(path: str, content: FileContent):
    try:
        fh.write_file(path, content.frontmatter, content.content)
        return {"status": "success"}
    except ValueError as e:
        return {"error": str(e)}


@router.patch("/write")
async def update_file(
    path: str, type: Literal["frontmatter", "content"], content: FileContent
):
    logger.info(f"Updating file at path: {path} with type: {type}")
    try:
        match type:
            case "frontmatter":
                fh.update_frontmatter(path, content.frontmatter)
            case "content":
                fh.update_content(path, content.content)

        return {"status": "success"}
    except ValueError as e:
        return {"error": str(e)}
