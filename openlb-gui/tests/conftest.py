import pytest
from backend.main import rate_limiter, read_rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """
    Automatically reset rate limiters before each test to prevent
    429 Too Many Requests errors from interfering with test logic.
    """
    rate_limiter.requests.clear()
    read_rate_limiter.requests.clear()
