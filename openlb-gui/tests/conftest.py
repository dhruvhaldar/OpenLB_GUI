import pytest
from backend.main import rate_limiter, read_rate_limiter
from collections import defaultdict, deque

@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """
    Resets the rate limiters before each test to prevent 429 errors
    caused by test execution speed.
    """
    rate_limiter.requests = defaultdict(deque)
    read_rate_limiter.requests = defaultdict(deque)
    yield
