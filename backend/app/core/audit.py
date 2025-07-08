"""
Audit decorators and middleware for automatic tracking
"""
import functools
import inspect
import logging
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from app.services.audit_service import AuditService
from app.core.deps import get_db

logger = logging.getLogger(__name__)

def audit_action(
    action: str,
    resource_type: str,
    description: Optional[str] = None,
    severity: str = "low",
    capture_args: bool = False,
    capture_result: bool = False
):
    """
    Decorator to automatically audit function calls
    
    Args:
        action: The action being performed
        resource_type: Type of resource being acted upon
        description: Optional description (can use {args} and {kwargs} placeholders)
        severity: Severity level of the action
        capture_args: Whether to capture function arguments in metadata
        capture_result: Whether to capture function result in metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract request context if available
            request = None
            db = None
            current_user = None
            
            # Look for these in function arguments
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):  # Request object
                    request = arg
                elif hasattr(arg, 'query'):  # Database session
                    db = arg
                elif hasattr(arg, 'id') and hasattr(arg, 'email'):  # User object
                    current_user = arg
            
            # Look for these in keyword arguments
            for key, value in kwargs.items():
                if key == 'request' and hasattr(value, 'method'):
                    request = value
                elif key == 'db' and hasattr(value, 'query'):
                    db = value
                elif key == 'current_user' and hasattr(value, 'id'):
                    current_user = value
            
            # If no DB session found, try to get one
            if db is None:
                try:
                    db = next(get_db())
                except:
                    logger.warning("Could not get database session for audit logging")
                    return await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Prepare audit data
            audit_data = {
                "action": action,
                "resource_type": resource_type,
                "severity": severity,
                "tpa_id": current_user.tpa_id if current_user else "system",
                "user_id": current_user.id if current_user else None,
            }
            
            # Add request context
            if request:
                audit_data.update({
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_path": str(request.url.path),
                    "request_method": request.method
                })
            
            # Prepare metadata
            metadata = {}
            if capture_args:
                metadata["function_args"] = str(args)
                metadata["function_kwargs"] = {k: str(v) for k, v in kwargs.items()}
            
            # Execute the function
            success = True
            error_message = None
            result = None
            
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                if capture_result and result is not None:
                    metadata["result_type"] = type(result).__name__
                    if hasattr(result, 'id'):
                        metadata["result_id"] = str(result.id)
                        audit_data["resource_id"] = str(result.id)
                
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
            
            finally:
                # Log the audit event
                try:
                    final_description = description or f"Function {func.__name__} executed"
                    if description and "{" in description:
                        # Replace placeholders
                        final_description = description.format(
                            args=args,
                            kwargs=kwargs,
                            result=result,
                            user=current_user.email if current_user else "system"
                        )
                    
                    audit_data.update({
                        "description": final_description,
                        "metadata": metadata if metadata else None,
                        "success": success,
                        "error_message": error_message
                    })
                    
                    await AuditService.log_event(db=db, **audit_data)
                    
                except Exception as audit_error:
                    logger.error(f"Failed to log audit event: {audit_error}")
            
            return result
        
        # For synchronous functions
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic but without async/await
            return func(*args, **kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def audit_endpoint(
    action: Optional[str] = None,
    resource_type: str = "api",
    severity: str = "low",
    track_performance: bool = True
):
    """
    Decorator specifically for FastAPI endpoints
    """
    def decorator(func: Callable) -> Callable:
        endpoint_action = action or f"{func.__name__}_endpoint"
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            # Extract common endpoint parameters
            request = kwargs.get('request')
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            # If no explicit current_user, look for it in dependencies
            if not current_user:
                for arg in args:
                    if hasattr(arg, 'id') and hasattr(arg, 'email'):
                        current_user = arg
                        break
            
            # Prepare audit data
            audit_data = {
                "action": endpoint_action,
                "resource_type": resource_type,
                "severity": severity,
                "tpa_id": current_user.tpa_id if current_user else "anonymous",
                "user_id": current_user.id if current_user else None,
                "description": f"API endpoint {func.__name__} called"
            }
            
            # Add request context
            if request:
                audit_data.update({
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_path": str(request.url.path),
                    "request_method": request.method
                })
            
            # Execute endpoint
            success = True
            error_message = None
            metadata = {}
            
            try:
                result = await func(*args, **kwargs)
                
                if track_performance:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds()
                    metadata["response_time_seconds"] = response_time
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            
            finally:
                # Log the audit event
                if db:
                    try:
                        audit_data.update({
                            "metadata": metadata if metadata else None,
                            "success": success,
                            "error_message": error_message
                        })
                        
                        await AuditService.log_event(db=db, **audit_data)
                        
                    except Exception as audit_error:
                        logger.error(f"Failed to log endpoint audit: {audit_error}")
        
        return wrapper
    return decorator

# Specific audit decorators for common actions
def audit_create(resource_type: str, description: Optional[str] = None):
    """Audit decorator for create operations"""
    return audit_action(
        action="create",
        resource_type=resource_type,
        description=description or f"Created {resource_type}",
        severity="medium",
        capture_result=True
    )

def audit_update(resource_type: str, description: Optional[str] = None):
    """Audit decorator for update operations"""
    return audit_action(
        action="update",
        resource_type=resource_type,
        description=description or f"Updated {resource_type}",
        severity="medium",
        capture_args=True,
        capture_result=True
    )

def audit_delete(resource_type: str, description: Optional[str] = None):
    """Audit decorator for delete operations"""
    return audit_action(
        action="delete",
        resource_type=resource_type,
        description=description or f"Deleted {resource_type}",
        severity="high",
        capture_args=True
    )

def audit_read(resource_type: str, description: Optional[str] = None):
    """Audit decorator for read operations (sensitive data)"""
    return audit_action(
        action="read",
        resource_type=resource_type,
        description=description or f"Read {resource_type}",
        severity="low"
    )

def audit_auth(action: str, description: Optional[str] = None):
    """Audit decorator for authentication events"""
    return audit_action(
        action=action,
        resource_type="authentication",
        description=description or f"Authentication: {action}",
        severity="medium"
    )

def audit_admin(action: str, description: Optional[str] = None):
    """Audit decorator for admin actions"""
    return audit_action(
        action=action,
        resource_type="admin",
        description=description or f"Admin action: {action}",
        severity="high",
        capture_args=True
    )

class AuditMiddleware:
    """
    Middleware to automatically track all API requests
    """
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        request = Request(scope, receive)
        start_time = datetime.utcnow()
        
        # Skip certain paths from audit logging
        path = request.url.path
        skip_paths = ["/api/v1/health", "/health", "/docs", "/openapi.json", "/favicon.ico"]
        should_audit = not any(path.startswith(skip_path) for skip_path in skip_paths)
        
        status_code = None
        error_message = None
        
        # Track the request
        async def send_wrapper(message):
            nonlocal status_code, error_message
            
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body" and should_audit:
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds()
                
                # Try to get database session and log the request
                try:
                    from app.core.deps import get_db
                    from app.services.audit_service import AuditService
                    
                    db = next(get_db())
                    
                    # Extract basic request info  
                    ip_address = None
                    if request.client:
                        ip_address = request.client.host
                    
                    user_agent = request.headers.get("user-agent", "")
                    
                    # Determine if this was a successful request
                    success = 200 <= status_code < 400
                    
                    # Create basic audit log for API access
                    await AuditService.log_event(
                        db=db,
                        tpa_id="system",  # Will be overridden by specific endpoints if user context available
                        action="api_request",
                        resource_type="api",
                        description=f"API request: {request.method} {path}",
                        severity="low",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_path=path,
                        request_method=request.method,
                        metadata={
                            "status_code": status_code,
                            "response_time": response_time,
                            "user_agent": user_agent
                        },
                        success=success,
                        error_message=f"HTTP {status_code}" if not success else None
                    )
                    
                    db.close()
                    
                except Exception as e:
                    # Don't let audit logging break the request
                    logger.warning(f"Failed to log API request audit: {e}")
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)