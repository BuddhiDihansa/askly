import pytest
from fastapi import HTTPException

from app.core.rate_limit import _hits, check_rate_limit


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    _hits.clear()
    yield
    _hits.clear()


def test_allows_requests_under_the_limit():
    for _ in range(5):
        check_rate_limit("test-key", max_per_minute=5)  # should not raise


def test_blocks_requests_over_the_limit():
    for _ in range(5):
        check_rate_limit("test-key", max_per_minute=5)

    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit("test-key", max_per_minute=5)
    assert exc_info.value.status_code == 429


def test_different_keys_have_independent_limits():
    for _ in range(5):
        check_rate_limit("user-1", max_per_minute=5)

    # user-2 should be unaffected by user-1 hitting their limit
    check_rate_limit("user-2", max_per_minute=5)  # should not raise
