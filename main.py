import os

from fastapi import FastAPI
from typing import Literal

from file_handler import FileHandler

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

fh = FileHandler(base_folder=BASE_DIR)


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the File Listing API!",
    }


@app.get("/list")
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
