from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_del_injection_fails():
    """
    Verifies that the DEL character (\x7f) is rejected.
    """
    # Payload with DEL character
    malicious_path = "my_cases/legit_case\x7f"

    # We expect a 400 Bad Request due to strict input validation
    response = client.post("/build", json={"case_path": malicious_path})

    # Assert that it IS rejected.
    assert response.status_code == 400
    assert "Invalid characters in path" in response.json()['detail']
