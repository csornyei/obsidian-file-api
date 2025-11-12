import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

""" Test cases for /v1/files/write PATCH endpoint:
    - update frontmatter
    - update content
    - error handling:
        absolute path
        non-existent file
"""


def test_update_frontmatter_success(
    client: TestClient, setup_temp_dir_content, temp_dir
):
    files = ["file1.md"]
    content = {
        "file1.md": "---\ntitle: Old Title\nauthor: Old Author\n---\nOld content."
    }

    setup_temp_dir_content(files, content)
    payload = {
        "frontmatter": {"title": "New Title", "author": "New Author"},
        "content": [],
    }

    response = client.patch(
        "/v1/files/write/",
        params={"path": "file1.md", "type": "frontmatter"},
        json=payload,
    )

    assert response.status_code == 204

    file_path = os.path.join(temp_dir, "file1.md")
    with open(file_path, "r") as f:
        file_content = f.read()
        assert (
            "---\ntitle: New Title\nauthor: New Author\n---\nOld content."
            == file_content
        )


def test_update_content_success(client: TestClient, setup_temp_dir_content, temp_dir):
    files = ["file1.md"]
    content = {
        "file1.md": "---\ntitle: Test File\nauthor: Test Author\n---\nOld content."
    }

    setup_temp_dir_content(files, content)
    payload = {
        "frontmatter": {},
        "content": ["This is the new content of the file."],
    }

    response = client.patch(
        "/v1/files/write/",
        params={"path": "file1.md", "type": "content"},
        json=payload,
    )

    assert response.status_code == 204

    file_path = os.path.join(temp_dir, "file1.md")
    with open(file_path, "r") as f:
        file_content = f.read()
        print(file_content)
        assert (
            "---\ntitle: Test File\nauthor: Test Author\n---\nOld content.\nThis is the new content of the file."
            == file_content
        )


def test_update_file_absolute_path(client: TestClient):
    payload = {
        "frontmatter": {"title": "Should Fail"},
        "content": ["This should fail."],
    }

    response = client.patch(
        "/v1/files/write/",
        params={"path": "/absolute/path/file.md", "type": "frontmatter"},
        json=payload,
    )

    assert response.status_code == 400
    assert response.json().get("message") == "The path must be a relative path."


def test_update_non_existent_file(client: TestClient):
    payload = {
        "frontmatter": {"title": "Nonexistent File"},
        "content": ["This should fail."],
    }

    response = client.patch(
        "/v1/files/write/",
        params={"path": "nonexistent_file.md", "type": "frontmatter"},
        json=payload,
    )

    assert response.status_code == 404
    assert (
        response.json().get("message")
        == "The provided path 'nonexistent_file.md' does not exist within the base folder."
    )
