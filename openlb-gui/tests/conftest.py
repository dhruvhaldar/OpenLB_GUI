import pytest
from backend.main import rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Reset the rate limiter before each test to prevent test pollution.
    """
    rate_limiter.requests.clear()
    yield
    rate_limiter.requests.clear()
