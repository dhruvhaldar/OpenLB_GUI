import time
from unittest.mock import patch
from backend.main import RateLimiter

def test_rate_limiter_global_reset():
    """
    Demonstrates the 'Global Reset' vulnerability in RateLimiter.
    When the cleanup interval passes, ALL history is wiped, even for recent requests.
    """
    # Note: RateLimiter now uses time.monotonic(), so we must patch that instead of time.time()
    with patch('time.monotonic') as mock_time:
        # Start at T=0
        mock_time.return_value = 0.0
        limiter = RateLimiter(requests_per_minute=2)

        # T=50: User A uses their full quota
        mock_time.return_value = 50.0
        assert limiter.is_rate_limited("192.168.1.1")[0] is False
        assert limiter.is_rate_limited("192.168.1.1")[0] is False
        assert limiter.is_rate_limited("192.168.1.1")[0] is True # Blocked

        # T=61: Cleanup Trigger
        # 61 seconds have passed since init (T=0), so cleanup runs.
        # The requests from T=50 are only 11 seconds old, so they SHOULD still count.
        # However, self.requests.clear() wipes them.
        mock_time.return_value = 61.0

        # Checking User B (or anyone) triggers the cleanup
        limiter.is_rate_limited("192.168.1.2")

        # Now check User A immediately.
        # If logic was correct: T=61. Requests at T=50. Age=11s. 11 < 60. Quota still full. Should be BLOCKED.
        # If vulnerable: History wiped. Allowed.
        is_blocked, retry_after = limiter.is_rate_limited("192.168.1.1")

        # Assert that it IS blocked, confirming the fix
        assert is_blocked is True, "Fix FAILED: User A was allowed despite exceeding quota."

        # Verify Retry-After calculation
        # Requests were at T=50. Window is 60s. Expires at T=110.
        # Now is T=61. Wait time = 110 - 61 = 49s.
        # Implementation adds +1 second for safety/rounding (ceil).
        assert retry_after == 50
