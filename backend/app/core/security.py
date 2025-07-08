"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def generate_password_reset_token() -> str:
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

def generate_verification_token() -> str:
    """Generate a secure email verification token"""
    return secrets.token_urlsafe(32)

class TokenData:
    """Token data structure"""
    def __init__(self, user_id: str, tpa_id: str, email: str, role: str, permissions: list = None):
        self.user_id = user_id
        self.tpa_id = tpa_id
        self.email = email
        self.role = role
        self.permissions = permissions or []

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency to get current user from JWT token
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            # Log authentication failure
            await _log_security_event(
                action="invalid_token",
                description="Token missing user ID",
                severity="medium"
            )
            raise AuthenticationError("Invalid token: missing user ID")
        
        token_data = TokenData(
            user_id=user_id,
            tpa_id=payload.get("tpa_id"),
            email=payload.get("email"),
            role=payload.get("role"),
            permissions=payload.get("permissions", [])
        )
        return token_data
    except JWTError as e:
        # Log authentication failure
        await _log_security_event(
            action="token_validation_failed",
            description=f"JWT validation failed: {str(e)}",
            severity="medium"
        )
        raise AuthenticationError("Could not validate credentials")

class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: TokenData = Depends(get_current_user_token)):
        if current_user.role not in self.allowed_roles:
            # Log authorization failure
            import asyncio
            asyncio.create_task(_log_security_event(
                action="access_denied",
                description=f"User {current_user.email} with role {current_user.role} attempted to access resource requiring roles: {', '.join(self.allowed_roles)}",
                severity="medium",
                user_id=current_user.user_id,
                tpa_id=current_user.tpa_id
            ))
            raise AuthorizationError(
                f"Operation requires one of these roles: {', '.join(self.allowed_roles)}"
            )
        return current_user

class PermissionChecker:
    """Permission-based access control checker"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    def __call__(self, current_user: TokenData = Depends(get_current_user_token)):
        if (self.required_permission not in current_user.permissions and 
            current_user.role != "tpa_admin"):  # Admin bypasses permission checks
            # Log permission denial
            import asyncio
            asyncio.create_task(_log_security_event(
                action="permission_denied",
                description=f"User {current_user.email} attempted to access resource requiring permission: {self.required_permission}",
                severity="medium",
                user_id=current_user.user_id,
                tpa_id=current_user.tpa_id
            ))
            raise AuthorizationError(
                f"Operation requires permission: {self.required_permission}"
            )
        return current_user

# Common role checkers
require_admin = RoleChecker(["tpa_admin"])
require_manager = RoleChecker(["tpa_admin", "cs_manager"])
require_agent = RoleChecker(["tpa_admin", "cs_manager", "cs_agent"])
require_authenticated = RoleChecker(["tpa_admin", "cs_manager", "cs_agent", "member", "readonly"])

# Common permission checkers
require_document_upload = PermissionChecker("document:upload")
require_user_management = PermissionChecker("user:manage")
require_analytics_access = PermissionChecker("analytics:read")


async def _log_security_event(
    action: str,
    description: str,
    severity: str = "medium",
    user_id: Optional[str] = None,
    tpa_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Internal function to log security events"""
    try:
        from app.core.database import get_db
        from app.services.audit_service import AuditService
        
        db = next(get_db())
        
        await AuditService.log_security_event(
            db=db,
            tpa_id=tpa_id or "system",
            action=action,
            description=description,
            user_id=user_id,
            severity=severity,
            metadata=metadata
        )
        
        db.close()
        
    except Exception as e:
        logger.warning(f"Failed to log security event: {e}")


async def log_authentication_failure(
    email: str,
    reason: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log authentication failure events"""
    await _log_security_event(
        action="authentication_failed",
        description=f"Failed login attempt for {email}: {reason}",
        severity="medium",
        metadata={
            "email": email,
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
    )


async def log_suspicious_activity(
    action: str,
    description: str,
    user_id: Optional[str] = None,
    tpa_id: Optional[str] = None,
    severity: str = "high",
    metadata: Optional[dict] = None
):
    """Log suspicious security activity"""
    await _log_security_event(
        action=action,
        description=description,
        severity=severity,
        user_id=user_id,
        tpa_id=tpa_id,
        metadata=metadata
    )