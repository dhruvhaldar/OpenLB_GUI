from fastapi.testclient import TestClient
from backend.main import app
import time

client = TestClient(app)

def test_rate_limit_get_cases():
    # We need to use a unique IP to avoid conflict with other tests
    client_ip = "192.168.1.100"

    # Try hitting it 100 times.
    # Current behavior: GET is NOT rate limited, so it should succeed 100 times.
    # Desired behavior: It should block after ~60 requests (if we increase limit)
    # or ~20 (if we keep it).

    blocked = False
    for i in range(100):
        # We must use a mocked IP to trigger the RateLimiter correctly if it relies on client.host
        # However, TestClient(app) is direct.
        # Middleware uses request.client.host.
        # We can fake it via scope if needed, but TestClient usually handles it.
        # But wait, we need to ensure the IP is consistent.

        # TestClient creates a new request each time.
        # Let's verify if RateLimiter sees the same IP.
        # Default TestClient host is "testclient".

        res = client.get("/cases")
        if res.status_code == 429:
            blocked = True
            break

    assert blocked, "GET requests should be rate limited"
