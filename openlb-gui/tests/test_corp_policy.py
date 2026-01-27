from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_corp_header():
    response = client.get("/cases")
    assert response.status_code == 200
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin", \
        "Missing Cross-Origin-Resource-Policy: same-origin"
