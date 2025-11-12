from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_full_file(client: TestClient, setup_temp_dir_content):
    files = ["file1.md"]
    content = {
        "file1.md": "---\ntitle: Test File\nauthor: Test Author\n---\nThis is the content of the file."
    }

    setup_temp_dir_content(files, content)

    response = client.get(
        "/v1/files/read/", params={"path": "file1.md", "type": "full"}
    )

    assert response.status_code == 200
    assert "content" in response.json()
    assert response.json()["content"] == content["file1.md"].split("\n")


def test_read_frontmatter(client: TestClient, setup_temp_dir_content):
    files = ["file1.md"]
    content = {
        "file1.md": "---\ntitle: Test File\nauthor: Test Author\n---\nThis is the content of the file."
    }

    setup_temp_dir_content(files, content)

    response = client.get(
        "/v1/files/read/", params={"path": "file1.md", "content": "frontmatter"}
    )

    print(response.json())

    assert response.status_code == 200
    assert "frontmatter" in response.json()
    assert response.json()["frontmatter"] == {
        "title": "Test File",
        "author": "Test Author",
    }


def test_read_text_content(client: TestClient, setup_temp_dir_content):
    files = ["file1.md"]
    content = {
        "file1.md": "---\ntitle: Test File\nauthor: Test Author\n---\nThis is the content of the file.\nThis is the second line."
    }

    setup_temp_dir_content(files, content)

    response = client.get(
        "/v1/files/read/", params={"path": "file1.md", "content": "text"}
    )

    assert response.status_code == 200
    assert "content" in response.json()
    assert response.json()["content"] == [
        "This is the content of the file.",
        "This is the second line.",
    ]


def test_read_frontmatter_no_frontmatter(client: TestClient, setup_temp_dir_content):
    files = ["file1.md"]
    content = {"file1.md": "This is the content of the file without frontmatter."}

    setup_temp_dir_content(files, content)

    response = client.get(
        "/v1/files/read/", params={"path": "file1.md", "content": "frontmatter"}
    )

    assert response.status_code == 200
    assert "frontmatter" in response.json()
    assert response.json()["frontmatter"] == {}


def test_read_file_invalid_path(client: TestClient):
    response = client.get(
        "/v1/files/read/", params={"path": "nonexistent.md", "content": "full"}
    )

    assert response.status_code == 404

    resp = response.json()

    assert "message" in resp
    assert (
        resp["message"]
        == "The provided path 'nonexistent.md' does not exist within the base folder."
    )


def test_read_file_absolute_path(client: TestClient):
    response = client.get(
        "/v1/files/read/", params={"path": "/absolute/path/file.md", "content": "full"}
    )

    resp = response.json()

    assert response.status_code == 400
    assert resp.get("message") == "The path must be a relative path."


def test_read_non_md_file(client: TestClient, setup_temp_dir_content):
    files = ["file1.txt"]
    content = {"file1.txt": "This is a text file."}

    setup_temp_dir_content(files, content)

    response = client.get(
        "/v1/files/read/", params={"path": "file1.txt", "content": "full"}
    )

    resp = response.json()

    assert response.status_code == 400
    assert resp.get("message") == "Only markdown (.md) files can be read."
