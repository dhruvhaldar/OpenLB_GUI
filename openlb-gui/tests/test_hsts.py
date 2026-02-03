from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_hsts_header_https():
    """
    Sentinel: Verify Strict-Transport-Security header is present on HTTPS requests.
    Protection: Prevents Protocol Downgrade Attacks and SSL Stripping.
    """
    # Simulate HTTPS request using base_url
    client_https = TestClient(app, base_url="https://testserver")
    response = client_https.get("/cases")

    assert response.status_code == 200
    hsts = response.headers.get("Strict-Transport-Security")
    expected = "max-age=63072000; includeSubDomains; preload"

    assert hsts is not None, "Strict-Transport-Security header missing on HTTPS request"
    assert hsts == expected, f"Incorrect HSTS value. Got: {hsts}"

def test_hsts_header_x_forwarded_proto():
    """
    Sentinel: Verify HSTS header is present when X-Forwarded-Proto is https.
    Usage: Common in reverse proxy setups (Nginx -> Uvicorn).
    """
    response = client.get("/cases", headers={"X-Forwarded-Proto": "https"})

    assert response.status_code == 200
    hsts = response.headers.get("Strict-Transport-Security")
    expected = "max-age=63072000; includeSubDomains; preload"

    assert hsts is not None, "Strict-Transport-Security header missing with X-Forwarded-Proto: https"
    assert hsts == expected, f"Incorrect HSTS value. Got: {hsts}"

def test_hsts_header_missing_on_http():
    """
    Sentinel: Verify HSTS header is NOT present on plain HTTP requests.
    Reason: HSTS is invalid/ignored on plain HTTP and could confuse some clients/scanners
    if they think the site claims to be secure but isn't.
    """
    response = client.get("/cases")

    assert response.status_code == 200
    hsts = response.headers.get("Strict-Transport-Security")
    assert hsts is None, "Strict-Transport-Security header present on HTTP request (Should be absent)"
