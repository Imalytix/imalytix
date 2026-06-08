import pytest

from app.utils.errors import SecurityViolationError
from app.utils.security import validate_safe_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/image.jpg",
        "http://localhost/image.jpg",
        "http://169.254.169.254/latest",
        "file:///etc/passwd",
        "chrome-extension://abc/image.png",
    ],
)
def test_blocked_urls(url):
    with pytest.raises(SecurityViolationError):
        validate_safe_url(url)

