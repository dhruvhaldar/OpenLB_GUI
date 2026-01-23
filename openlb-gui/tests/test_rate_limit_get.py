from fastapi.testclient import TestClient
from backend.main import app, read_rate_limiter

client = TestClient(app)

def test_get_rate_limit():
    """
    Verifies that GET requests are rate limited after 100 requests.
    """
    # Clean up the limiter before test to ensure clean state
    read_rate_limiter.requests.clear()

    # 1. Send 100 requests (allowed)
    # We use /cases as the target endpoint
    for i in range(100):
        response = client.get("/cases")
        # Ensure we are not blocked yet.
        # Note: We expect 200 (if cases exist) or 200 (empty list).
        # We accept any 2xx success.
        assert response.status_code == 200, f"Request {i+1} failed with {response.status_code}"

    # 2. Send the 101st request (should be blocked)
    response = client.get("/cases")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Please try again later."

    # Clean up after test
    read_rate_limiter.requests.clear()
