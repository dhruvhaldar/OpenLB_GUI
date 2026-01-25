import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app

client = TestClient(app)

def test_read_rate_limiting():
    """
    Verifies that GET requests are rate-limited using the read_rate_limiter.
    """
    # We patch 'backend.main.read_rate_limiter' which we expect to add.
    # If the variable doesn't exist, this patch will fail (AttributeError).
    # This is expected until we implement the fix.
    try:
        with patch("backend.main.read_rate_limiter") as mock_limiter:
            # Scenario: First 2 requests allowed, 3rd blocked
            # False = Not limited, True = Limited
            mock_limiter.is_rate_limited.side_effect = [False, False, True]

            # 1. Allowed
            res1 = client.get("/cases")
            assert res1.status_code == 200

            # 2. Allowed
            res2 = client.get("/cases")
            assert res2.status_code == 200

            # 3. Blocked
            res3 = client.get("/cases")
            assert res3.status_code == 429
            assert "Too many requests" in res3.json()["detail"]
    except AttributeError:
        # This catch block is just to allow the test file to be created without
        # crashing if someone tries to import it before the fix.
        # But 'patch' usually resolves at runtime.
        pytest.fail("read_rate_limiter not found in backend.main (Fix not implemented yet)")
