from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_permissions_policy_enhancement():
    """
    Verify that the Permissions-Policy header includes strict directives.
    Sentinel Enhancement: Disable powerful browser features not needed by the app.
    """
    response = client.get("/cases")
    assert response.status_code == 200

    policy = response.headers.get("Permissions-Policy")
    assert policy is not None, "Permissions-Policy header is missing"

    # Check for newly added directives
    assert "midi=()" in policy
    assert "sync-xhr=()" in policy
    assert "accelerometer=()" in policy
    assert "gyroscope=()" in policy
    assert "magnetometer=()" in policy
    assert "fullscreen=()" in policy
    assert "picture-in-picture=()" in policy

    # Check for original directives
    assert "geolocation=()" in policy
    assert "microphone=()" in policy
    assert "camera=()" in policy
    assert "payment=()" in policy
    assert "usb=()" in policy
    assert "vr=()" in policy
    assert "autoplay=()" in policy

def test_cache_control():
    """
    Verify Cache-Control is no-store.
    """
    response = client.get("/cases")
    assert response.headers.get("Cache-Control") == "no-store"
