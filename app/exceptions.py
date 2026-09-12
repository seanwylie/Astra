"""
Astra-specific exceptions for config, mind load/save, and external services.
Use these so callers can catch and handle specific failure modes.
"""


class AstraException(Exception):
    """Base exception for Astra application errors."""

    pass


class ConfigurationError(AstraException):
    """Raised when required configuration is missing or invalid."""

    pass


class InfluenceError(AstraException):
    """Raised when mind load or save (S3/influence) fails."""

    pass


class ExternalServiceError(AstraException):
    """Raised when an external service (e.g. OpenAI, S3) call fails after retries."""

    pass
