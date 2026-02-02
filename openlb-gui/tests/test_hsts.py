from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_hsts_header_https():
    """Verify HSTS header is present for HTTPS requests."""
    # Simulate HTTPS request via X-Forwarded-Proto
    response = client.get("/cases", headers={"X-Forwarded-Proto": "https"})
    assert response.status_code == 200
    assert "Strict-Transport-Security" in response.headers, "HSTS header missing on HTTPS request"
    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains; preload"

def test_hsts_header_http():
    """Verify HSTS header is ABSENT for HTTP requests."""
    # Simulate HTTP request
    response = client.get("/cases", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code == 200
    assert "Strict-Transport-Security" not in response.headers, "HSTS header should not be present on HTTP request"
