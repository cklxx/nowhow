"""
Custom exception classes for the application.
"""


class AppException(Exception):
    """Base exception for application errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(AppException):
    """Raised when there's a configuration error."""
    pass


class ModelServiceError(AppException):
    """Raised when there's an error with model services."""
    pass


class SourceNotFoundError(AppException):
    """Raised when a source is not found."""
    pass


class ValidationError(AppException):
    """Raised when validation fails."""
    pass


class CrawlingError(AppException):
    """Raised when content crawling fails."""
    pass


class ProcessingError(AppException):
    """Raised when content processing fails."""
    pass


class StorageError(AppException):
    """Raised when storage operations fail."""
    pass


class WorkflowError(AppException):
    """Raised when workflow execution fails."""
    pass


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    pass