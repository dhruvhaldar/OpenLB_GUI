from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_corp_header():
    """
    Verifies that the Cross-Origin-Resource-Policy header is set to 'same-origin'.
    """
    response = client.get("/cases")
    assert response.status_code == 200
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"

def test_control_char_validation_del():
    """
    Verifies that paths with the DEL character (\x7f) are rejected.
    """
    # Payload with a DEL character
    malicious_path = "my_cases/legit_case\x7fINJECTED"

    # We expect a 400 Bad Request
    response = client.post("/build", json={"case_path": malicious_path})
    assert response.status_code == 400
    assert "Invalid characters in path" in response.json()['detail']
