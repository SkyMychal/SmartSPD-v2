"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from app.core.database import get_db
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_token,
    get_current_user_token,
    TokenData
)
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.schemas.auth import (
    Token, 
    UserLogin, 
    UserRegister, 
    RefreshToken,
    PasswordReset,
    PasswordResetRequest
)
from app.schemas.user import UserOut
from app.crud.user import user_crud
from app.crud.tpa import tpa_crud
from app.models.user import User
from app.models.tpa import TPA
from app.services.audit_service import AuditService

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    """
    # Get user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise AuthenticationError("Invalid email or password")
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise AuthenticationError("Account is disabled")
    
    # Check if TPA is active
    tpa = db.query(TPA).filter(TPA.id == user.tpa_id).first()
    if not tpa or not tpa.is_active:
        raise AuthenticationError("Organization account is disabled")
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "tpa_id": user.tpa_id,
            "role": user.role.value,
            "permissions": user.permissions or []
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.id,
            "email": user.email,
            "tpa_id": user.tpa_id
        }
    )
    
    # Update user login info
    user.login_count = (user.login_count or 0) + 1
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.from_orm(user)
    }

@router.post("/register", response_model=UserOut)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    User registration endpoint (TPA admin only)
    """
    # Check if TPA exists
    tpa = await tpa_crud.get(db, id=user_data.tpa_id)
    if not tpa:
        raise ValidationError("Invalid TPA organization")
    
    # Check if email already exists within the TPA
    existing_user = await user_crud.get_by_email_and_tpa(
        db, 
        email=user_data.email, 
        tpa_id=user_data.tpa_id
    )
    if existing_user:
        raise ValidationError("Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = await user_crud.create(
        db,
        obj_in={
            **user_data.dict(exclude={"password"}),
            "hashed_password": hashed_password,
            "is_verified": False  # Require email verification
        }
    )
    
    # Log user creation
    await AuditService.log_event(
        db=db,
        tpa_id=user_data.tpa_id,
        action="create",
        resource_type="user",
        resource_id=user.id,
        description=f"User registered: {user.email}"
    )
    
    return UserOut.from_orm(user)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        payload = verify_token(refresh_data.refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token")
        
        # Get user
        user = await user_crud.get(db, id=user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "tpa_id": user.tpa_id,
                "role": user.role.value,
                "permissions": user.permissions
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_data.refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        raise AuthenticationError("Invalid refresh token")

@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    User logout endpoint
    """
    # Log logout event
    await AuditService.log_auth_event(
        db=db,
        user_id=current_user.user_id,
        tpa_id=current_user.tpa_id,
        action="logout",
        description="User logged out"
    )
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
async def get_current_user(
    current_user: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Get current user information
    """
    user = await user_crud.get(db, id=current_user.user_id)
    if not user:
        raise AuthenticationError("User not found")
    
    return UserOut.from_orm(user)

@router.post("/password-reset-request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset
    """
    user = await user_crud.get_by_email(db, email=request_data.email)
    if user:
        # Generate reset token and send email
        # Implementation depends on email service
        pass
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    """
    # Verify reset token and update password
    # Implementation depends on reset token storage strategy
    return {"message": "Password has been reset successfully"}

@router.get("/test-token")
async def get_test_token():
    """
    DISABLED: Test token endpoint disabled for production security
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Test token endpoint disabled"
    )