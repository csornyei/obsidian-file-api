import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_write_file_success(client: TestClient, temp_dir):
    payload = {
        "frontmatter": {"title": "New File", "author": "Test Author", "tags": ["test"]},
        "content": ["This is the content of the new file."],
    }

    response = client.post(
        "/v1/files/write/", params={"path": "new_file.md"}, json=payload
    )

    assert response.status_code == 201
    assert response.json().get("status") == "success"

    file_path = os.path.join(temp_dir, "new_file.md")
    assert os.path.exists(file_path)
    with open(file_path, "r") as f:
        file_content = f.read()
        assert (
            "---\ntitle: New File\nauthor: Test Author\ntags:\n- test\n---\nThis is the content of the new file."
            == file_content
        )


def test_write_file_overwrite_not_allowed(client: TestClient, setup_temp_dir_content):
    files = ["existing_file.md"]
    setup_temp_dir_content(files)

    payload = {
        "frontmatter": {"title": "Existing File"},
        "content": ["This is new content."],
    }

    response = client.post(
        "/v1/files/write/", params={"path": "existing_file.md"}, json=payload
    )

    assert response.status_code == 400
    assert (
        response.json().get("message")
        == "The file 'existing_file.md' already exists. Overwriting is not allowed."
    )


def test_write_file_absolute_path(client: TestClient):
    payload = {
        "frontmatter": {"title": "Absolute Path File"},
        "content": ["This should fail."],
    }

    response = client.post(
        "/v1/files/write/", params={"path": "/absolute/path/file.md"}, json=payload
    )

    assert response.status_code == 400
    assert response.json().get("message") == "The path must be a relative path."


def test_write_file_nonexistent_directory(client: TestClient):
    payload = {
        "frontmatter": {"title": "Nonexistent Dir File"},
        "content": ["This should fail."],
    }

    response = client.post(
        "/v1/files/write/", params={"path": "nonexistent_dir/file.md"}, json=payload
    )

    assert response.status_code == 404
    assert (
        response.json().get("message")
        == "The directory 'nonexistent_dir' does not exist within the base folder."
    )
