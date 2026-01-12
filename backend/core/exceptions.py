"""Custom exception classes for the Restaurant Reservation System."""

class BusinessLogicError(Exception):
    """Raised when business logic validation fails."""
    pass


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ConflictError(Exception):
    """Raised when a resource conflict occurs (e.g., double booking)."""
    pass
