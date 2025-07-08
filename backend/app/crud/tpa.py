"""
TPA CRUD operations
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.tpa import TPA
from app.schemas.tpa import TPACreate, TPAUpdate

class CRUDTPA(CRUDBase[TPA, TPACreate, TPAUpdate]):
    
    async def get_by_slug(self, db: Session, *, slug: str) -> Optional[TPA]:
        """Get TPA by slug"""
        return db.query(TPA).filter(TPA.slug == slug).first()
    
    async def get_active(self, db: Session) -> list[TPA]:
        """Get all active TPAs"""
        return db.query(TPA).filter(TPA.is_active == True).all()
    
    async def create_with_slug(self, db: Session, *, obj_in: TPACreate) -> TPA:
        """Create TPA and auto-generate slug if not provided"""
        create_data = obj_in.dict()
        
        if not create_data.get("slug"):
            # Generate slug from name
            base_slug = create_data["name"].lower().replace(" ", "-").replace("_", "-")
            # Remove special characters
            import re
            base_slug = re.sub(r'[^a-z0-9-]', '', base_slug)
            
            # Ensure uniqueness
            counter = 1
            slug = base_slug
            while await self.get_by_slug(db, slug=slug):
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            create_data["slug"] = slug
        
        db_obj = TPA(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

tpa_crud = CRUDTPA(TPA)