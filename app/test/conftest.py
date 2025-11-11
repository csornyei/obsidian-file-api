import os
import pytest
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.main import app
from app.file_handler import get_file_handler, FileHandler


@pytest.fixture()
def temp_dir():
    with TemporaryDirectory() as tmp_path:
        yield tmp_path


@pytest.fixture
def setup_temp_dir_content(temp_dir):
    def setup_content(files: list[str], content: dict[str, str] = None):
        content = content or {}
        for file in files:
            file_path = os.path.join(temp_dir, file)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content.get(file, "."))

    yield setup_content


@pytest.fixture
def client(temp_dir):
    def override_get_file_handler() -> FileHandler:
        return FileHandler(base_folder=temp_dir)

    app.dependency_overrides[get_file_handler] = override_get_file_handler
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
