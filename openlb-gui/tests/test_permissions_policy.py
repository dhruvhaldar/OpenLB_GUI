from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_permissions_policy_header():
    """
    Sentinel: Verify that the Permissions-Policy header includes all strict directives.
    Defense in Depth: Explicitly disabling powerful features reduces the attack surface.
    """
    response = client.get("/cases")
    assert response.status_code == 200

    policy = response.headers.get("Permissions-Policy", "")
    assert policy, "Permissions-Policy header is missing"

    # List of directives that must be disabled (=())
    required_directives = [
        "geolocation",
        "microphone",
        "camera",
        "payment",
        "usb",
        "vr",
        "autoplay",
        "midi",
        "sync-xhr",
        "accelerometer",
        "gyroscope",
        "magnetometer",
        "fullscreen",
        "picture-in-picture"
    ]

    for directive in required_directives:
        expected = f"{directive}=()"
        assert expected in policy, f"Permissions-Policy missing strict directive: {expected}. Current policy: {policy}"
