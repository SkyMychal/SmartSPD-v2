"""
User management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_token, require_manager, TokenData
from app.core.audit import audit_endpoint, audit_read
from app.schemas.user import UserOut, UserUpdate, UserList
from app.crud.user import user_crud

router = APIRouter()

@router.get("/", response_model=UserList)
@audit_endpoint(action="list_users", resource_type="user", severity="medium")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """List users in TPA"""
    users = await user_crud.get_multi_by_tpa(
        db, tpa_id=current_user.tpa_id, skip=skip, limit=limit
    )
    total = await user_crud.count_by_tpa(db, tpa_id=current_user.tpa_id)
    
    return UserList(
        users=[UserOut.from_orm(user) for user in users],
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{user_id}", response_model=UserOut)
@audit_endpoint(action="get_user", resource_type="user", severity="low")
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = await user_crud.get_by_tpa(db, tpa_id=current_user.tpa_id, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserOut.from_orm(user)