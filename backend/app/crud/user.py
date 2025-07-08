"""
User CRUD operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import TenantCRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from datetime import datetime

class CRUDUser(TenantCRUDBase[User, UserCreate, UserUpdate]):
    
    async def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email (across all TPAs for login)"""
        return db.query(User).filter(User.email == email).first()
    
    async def get_by_email_and_tpa(
        self, 
        db: Session, 
        *, 
        email: str, 
        tpa_id: str
    ) -> Optional[User]:
        """Get user by email within specific TPA"""
        return db.query(User).filter(
            and_(
                User.email == email,
                User.tpa_id == tpa_id
            )
        ).first()
    
    async def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create user with hashed password"""
        create_data = obj_in.dict()
        create_data["hashed_password"] = get_password_hash(create_data.pop("password"))
        
        db_obj = User(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    async def update_password(
        self, 
        db: Session, 
        *, 
        user: User, 
        new_password: str
    ) -> User:
        """Update user password"""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    async def update_login_info(self, db: Session, *, user_id: str) -> User:
        """Update user login information"""
        user = await self.get(db, id=user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    async def search_users(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by name or email within TPA"""
        search_filter = or_(
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
        
        return db.query(User).filter(
            and_(
                User.tpa_id == tpa_id,
                search_filter
            )
        ).offset(skip).limit(limit).all()
    
    async def get_active_users_count(self, db: Session, *, tpa_id: str) -> int:
        """Get count of active users for a TPA"""
        return db.query(User).filter(
            and_(
                User.tpa_id == tpa_id,
                User.is_active == True
            )
        ).count()
    
    async def get_by_tpa(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by TPA"""
        return db.query(User).filter(
            User.tpa_id == tpa_id
        ).offset(skip).limit(limit).all()

user_crud = CRUDUser(User)