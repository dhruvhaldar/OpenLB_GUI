from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_del_char_rejection():
    """
    Verifies that paths with the DEL character (\\x7f) are rejected.
    """
    # Payload with DEL character
    malicious_path = "my_cases/legit_case\x7fINJECTED"

    # We use /build as it calls validate_case_path
    response = client.post("/build", json={"case_path": malicious_path})

    # After fix: This MUST return 400 (Invalid characters)
    assert response.status_code == 400
    assert "Invalid characters in path" in response.json()['detail']

def test_security_headers_enhancement():
    """
    Verifies that new security headers are present.
    """
    response = client.get("/cases")
    assert response.status_code == 200
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
