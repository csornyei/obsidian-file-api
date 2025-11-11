from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_files(client: TestClient, setup_temp_dir_content):
    files = ["file1.md", "file2.md", "file3.md"]
    setup_temp_dir_content(files)

    response = client.get("/v1/files/", params={"path": "", "type": "files_all"})

    assert response.status_code == 200

    assert isinstance(response.json(), list)
    assert set(response.json()) == set(files)
