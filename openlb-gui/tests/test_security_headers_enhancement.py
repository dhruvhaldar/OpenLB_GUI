from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_new_security_headers():
    response = client.get("/cases")
    assert response.status_code == 200

    # Check for X-Permitted-Cross-Domain-Policies
    assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none", \
        "Missing X-Permitted-Cross-Domain-Policies: none"

    # Check for Cross-Origin-Opener-Policy
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin", \
        "Missing Cross-Origin-Opener-Policy: same-origin"

    # Check for Strict-Transport-Security
    assert response.headers.get("Strict-Transport-Security") == "max-age=63072000; includeSubDomains; preload", \
        "Missing or incorrect Strict-Transport-Security header"
