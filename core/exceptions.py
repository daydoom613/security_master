"""
Custom exceptions for AlfaGrow Security Service
"""
from typing import Optional, Dict, Any


class SecurityServiceError(Exception):
    """Base exception for Security Service"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SecurityNotFoundError(SecurityServiceError):
    """Raised when a security is not found"""
    
    def __init__(self, identifier: str, search_type: str = "unknown"):
        self.identifier = identifier
        self.search_type = search_type
        message = f"Security not found for {search_type}: {identifier}"
        super().__init__(message, {"identifier": identifier, "search_type": search_type})


class InvalidInputError(SecurityServiceError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, {"field": field})


class DatabaseError(SecurityServiceError):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: str = "unknown"):
        self.operation = operation
        super().__init__(message, {"operation": operation})


class ProwessAPIError(SecurityServiceError):
    """Raised when Prowess API operations fail"""
    
    def __init__(self, message: str, operation: str = "unknown"):
        self.operation = operation
        super().__init__(message, {"operation": operation})


class S3Error(SecurityServiceError):
    """Raised when S3 operations fail"""
    
    def __init__(self, message: str, operation: str = "unknown"):
        self.operation = operation
        super().__init__(message, {"operation": operation})


class AbbreviationExpansionError(SecurityServiceError):
    """Raised when abbreviation expansion fails"""
    
    def __init__(self, message: str, abbreviation: str = "unknown"):
        self.abbreviation = abbreviation
        super().__init__(message, {"abbreviation": abbreviation})
