"""
Dependency injection utilities for the application
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user_token, TokenData
from app.crud.user import user_crud
from app.models.user import User

def get_db() -> Generator:
    """Database dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_token)
) -> User:
    """Get current user from token"""
    user = await user_crud.get(db, id=token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    return user

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role for access"""
    if current_user.role != "tpa_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require manager role or higher for access"""
    if current_user.role not in ["tpa_admin", "cs_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user

async def require_agent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require agent role or higher for access"""
    if current_user.role not in ["tpa_admin", "cs_manager", "cs_agent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent access required"
        )
    return current_user

async def require_same_tpa(
    tpa_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user belongs to the same TPA"""
    if current_user.tpa_id != tpa_id and current_user.role != "tpa_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: different TPA"
        )
    return current_user