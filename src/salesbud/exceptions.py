"""
SalesBud Custom Exceptions

Defines the exception hierarchy for the SalesBud application.
All custom exceptions inherit from SalesBudError.
"""


class SalesBudError(Exception):
    """Base exception for all SalesBud errors."""

    pass


class ValidationError(SalesBudError):
    """Raised when input validation fails."""

    pass


class DatabaseError(SalesBudError):
    """Raised when a database operation fails."""

    pass


class LinkedInError(SalesBudError):
    """Raised when LinkedIn automation fails."""

    pass


class EmailError(SalesBudError):
    """Raised when email operations fail."""

    pass


class RateLimitError(SalesBudError):
    """Raised when rate limits are exceeded."""

    pass
