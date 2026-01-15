from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dns_rebinding_protection():
    """
    Simulate a DNS Rebinding attack where the attacker accesses the API
    using a malicious hostname (rebound to 127.0.0.1).
    """
    # 1. Normal access (should succeed)
    # explicitly setting Host to allowed values
    response = client.get("/cases", headers={"Host": "localhost"})
    assert response.status_code == 200

    response = client.get("/cases", headers={"Host": "127.0.0.1"})
    assert response.status_code == 200

    # 2. Malicious Host access (should be blocked)
    # Attempt to access with an arbitrary domain (DNS Rebinding scenario)
    response = client.get("/cases", headers={"Host": "attacker.com"})

    # TrustedHostMiddleware returns 400 Bad Request for invalid hosts
    assert response.status_code == 400
