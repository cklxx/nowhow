"""
Core module containing dependency injection, interfaces, and base classes.
"""

from .dependency_container import Container, get_container
from .interfaces import IModelService, IStorageService, ISourceRepository
from .exceptions import (
    AppException,
    ConfigurationError,
    ModelServiceError,
    SourceNotFoundError,
    ValidationError
)

__all__ = [
    "Container",
    "get_container",
    "IModelService",
    "IStorageService", 
    "ISourceRepository",
    "AppException",
    "ConfigurationError",
    "ModelServiceError",
    "SourceNotFoundError",
    "ValidationError"
]