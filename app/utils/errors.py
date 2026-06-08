class ImalytixError(Exception):
    """Base error for Imalytix services."""


class ImageValidationError(ImalytixError):
    """Raised when uploaded image validation fails."""


class SecurityViolationError(ImalytixError):
    """Raised when a URL fails SSRF or security checks."""


class OpenAIServiceError(ImalytixError):
    """Raised when the OpenAI vision service cannot produce a result."""

