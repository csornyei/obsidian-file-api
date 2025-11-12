from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_files(client: TestClient, setup_temp_dir_content):
    files = ["file1.md", "file2.md", "file3.md", "dir1/file4.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "files"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(["file1.md", "file2.md", "file3.md"])


def test_list_dirs(client: TestClient, setup_temp_dir_content):
    files = ["dir1/file1.md", "dir2/file2.md", "dir3/dir4/file3.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "dirs"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(["dir1", "dir2", "dir3"])


def test_list_all_files(client: TestClient, setup_temp_dir_content):
    files = ["file1.md", "file2.md", "file3.md", "dir1/file4.md", "dir2/file5.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "files_all"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(files)


def test_list_all_dirs(client: TestClient, setup_temp_dir_content):
    files = ["dir1/file1.md", "dir2/file2.md", "dir3/dir4/file3.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "dirs_all"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(["dir1", "dir2", "dir3", "dir3/dir4"])


def test_list_files_with_path_filter(client: TestClient, setup_temp_dir_content):
    files = ["dir1/file1.md", "dir1/file2.md", "dir2/file3.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "dir1", "type": "files"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(["dir1/file1.md", "dir1/file2.md"])


def test_list_files_invalid_path(client: TestClient):
    response = client.get("/v1/files/", params={"path": "nonexistent", "type": "files"})

    resp = response.json()

    assert response.status_code == 404
    assert (
        resp.get("message")
        == "The provided path 'nonexistent' does not exist within the base folder."
    )


def test_list_files_absolute_path(client: TestClient):
    response = client.get(
        "/v1/files/", params={"path": "/absolute/path", "type": "files"}
    )

    resp = response.json()

    assert response.status_code == 400
    assert resp.get("message") == "The path must be a relative path."


def test_list_files_invalid_type(client: TestClient):
    response = client.get("/v1/files/", params={"path": "", "type": "invalid_type"})

    assert response.status_code == 422

    resp = response.json()

    error_details = resp.get("detail", [])

    assert len(error_details) == 1
    detail = error_details[0]

    assert "invalid_type" == detail.get("input")
    assert "Input should be 'files', 'files_all', 'dirs' or 'dirs_all'" == detail.get(
        "msg"
    )


def test_list_files_filter_non_markdown(client: TestClient, setup_temp_dir_content):
    files = ["file1.md", "file2.txt", "file3.md", "dir1/file4.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "files"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(["file1.md", "file3.md"])
