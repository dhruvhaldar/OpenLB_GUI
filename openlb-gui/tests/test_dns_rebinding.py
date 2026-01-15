
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dns_rebinding_rejected():
    """
    Verifies that the server rejects requests with malicious Host headers.
    This protects against DNS Rebinding attacks where an attacker controls
    a domain that resolves to 127.0.0.1.
    """
    # 1. Valid Host should be accepted
    response = client.get("/cases", headers={"Host": "localhost"})
    assert response.status_code == 200

    # 2. Malicious Host should be rejected
    # Without TrustedHostMiddleware, this currently returns 200 (or whatever the endpoint returns)
    response = client.get("/cases", headers={"Host": "attacker.com"})

    # We expect 400 Bad Request once the protection is added
    assert response.status_code == 400
