"""
Token refresh middleware for automatic token management
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from datetime import datetime, timedelta
from .security import create_access_token, verify_token
from .config import settings
import logging

logger = logging.getLogger(__name__)

class TokenRefreshMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically refresh tokens when they're close to expiration
    """
    
    def __init__(self, app, refresh_threshold_minutes: int = 60):
        super().__init__(app)
        self.refresh_threshold_minutes = refresh_threshold_minutes
    
    async def dispatch(self, request: Request, call_next):
        """
        Check if token needs refreshing and automatically refresh if needed
        """
        # Skip token refresh for certain endpoints
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/auth/login"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        token = auth_header.split(" ")[1]
        
        try:
            # Decode token without verification to check expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                now = datetime.utcnow()
                time_until_expiry = exp_datetime - now
                
                # If token expires within threshold, generate new token
                if time_until_expiry.total_seconds() < (self.refresh_threshold_minutes * 60):
                    logger.info(f"Token expires in {time_until_expiry}, refreshing...")
                    
                    try:
                        # Verify the current token is still valid
                        verify_token(token)
                        
                        # Create new token with same payload (but fresh expiration)
                        new_token = create_access_token(
                            data={
                                "sub": payload.get("sub"),
                                "email": payload.get("email"),
                                "tpa_id": payload.get("tpa_id"),
                                "role": payload.get("role"),
                                "permissions": payload.get("permissions", [])
                            },
                            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                        )
                        
                        # Update request headers with new token
                        request.headers.__dict__["_list"] = [
                            (name, value) if name != b"authorization" 
                            else (name, f"Bearer {new_token}".encode())
                            for name, value in request.headers.raw
                        ]
                        
                        # Process request
                        response = await call_next(request)
                        
                        # Add new token to response headers
                        response.headers["X-New-Token"] = new_token
                        response.headers["X-Token-Refreshed"] = "true"
                        
                        return response
                        
                    except Exception as e:
                        logger.warning(f"Token refresh failed: {e}")
                        # Continue with original token
                        pass
        
        except Exception as e:
            logger.debug(f"Token check failed: {e}")
            # Continue with original request
            pass
        
        return await call_next(request)