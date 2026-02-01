from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_hsts_header_present_https():
    """
    Verify that HSTS header is present when X-Forwarded-Proto is https.
    """
    response = client.get("/cases", headers={"X-Forwarded-Proto": "https"})
    assert response.status_code == 200
    hsts = response.headers.get("Strict-Transport-Security")
    assert hsts == "max-age=63072000; includeSubDomains; preload"

def test_hsts_header_absent_http():
    """
    Verify that HSTS header is absent when using http.
    """
    response = client.get("/cases", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code == 200
    assert "Strict-Transport-Security" not in response.headers
