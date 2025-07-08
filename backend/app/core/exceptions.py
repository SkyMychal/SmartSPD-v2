"""
Custom exceptions for SmartSPD
"""
from typing import Any, Dict, Optional

class SmartSPDException(Exception):
    """Base exception for SmartSPD application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "SMARTSPD_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(SmartSPDException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_type="AUTHENTICATION_ERROR",
            details=details
        )

class AuthorizationError(SmartSPDException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_type="AUTHORIZATION_ERROR",
            details=details
        )

class ValidationError(SmartSPDException):
    """Validation related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_type="VALIDATION_ERROR",
            details=details
        )

class NotFoundError(SmartSPDException):
    """Resource not found errors"""
    
    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            status_code=404,
            error_type="NOT_FOUND_ERROR",
            details={"resource": resource, "resource_id": resource_id}
        )

class ConflictError(SmartSPDException):
    """Resource conflict errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_type="CONFLICT_ERROR",
            details=details
        )

class TenantAccessError(SmartSPDException):
    """Multi-tenant access violations"""
    
    def __init__(self, message: str = "Access to this resource is not allowed for your organization"):
        super().__init__(
            message=message,
            status_code=403,
            error_type="TENANT_ACCESS_ERROR"
        )

class DocumentProcessingError(SmartSPDException):
    """Document processing related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_type="DOCUMENT_PROCESSING_ERROR",
            details=details
        )

class AIServiceError(SmartSPDException):
    """AI service related errors"""
    
    def __init__(self, message: str, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=503,
            error_type="AI_SERVICE_ERROR",
            details={**(details or {}), "service": service}
        )

class RateLimitError(SmartSPDException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            status_code=429,
            error_type="RATE_LIMIT_ERROR",
            details=details
        )