from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_files():
    response = client.get("/v1/files/", params={"path": "", "type": "files_all"})
    assert isinstance(response.json(), list)
    print(response.json())
    assert response.status_code == 100
