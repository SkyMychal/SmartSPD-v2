"""
Health Plan CRUD operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import TenantCRUDBase
from app.models.health_plan import HealthPlan
from app.schemas.health_plan import HealthPlanCreate, HealthPlanUpdate

class CRUDHealthPlan(TenantCRUDBase[HealthPlan, HealthPlanCreate, HealthPlanUpdate]):
    
    async def get_by_plan_number(
        self, 
        db: Session, 
        *, 
        plan_number: str,
        tpa_id: str
    ) -> Optional[HealthPlan]:
        """Get health plan by plan number within TPA"""
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.plan_number == plan_number,
                HealthPlan.tpa_id == tpa_id
            )
        ).first()
    
    async def get_active_plans(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[HealthPlan]:
        """Get active health plans for TPA"""
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.tpa_id == tpa_id,
                HealthPlan.is_active == True
            )
        ).offset(skip).limit(limit).all()
    
    async def search_plans(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[HealthPlan]:
        """Search health plans by name or plan number"""
        search_filter = or_(
            HealthPlan.name.ilike(f"%{query}%"),
            HealthPlan.plan_number.ilike(f"%{query}%"),
            HealthPlan.description.ilike(f"%{query}%")
        )
        
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.tpa_id == tpa_id,
                search_filter
            )
        ).offset(skip).limit(limit).all()
    
    async def get_plans_by_year(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        plan_year: int
    ) -> List[HealthPlan]:
        """Get health plans for specific year"""
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.tpa_id == tpa_id,
                HealthPlan.plan_year == plan_year
            )
        ).all()
    
    async def get_plan_stats(
        self, 
        db: Session, 
        *, 
        tpa_id: str
    ) -> dict:
        """Get health plan statistics"""
        from sqlalchemy import func
        
        total = db.query(func.count(HealthPlan.id)).filter(
            HealthPlan.tpa_id == tpa_id
        ).scalar()
        
        active = db.query(func.count(HealthPlan.id)).filter(
            and_(
                HealthPlan.tpa_id == tpa_id,
                HealthPlan.is_active == True
            )
        ).scalar()
        
        processing_completed = db.query(func.count(HealthPlan.id)).filter(
            and_(
                HealthPlan.tpa_id == tpa_id,
                HealthPlan.processing_status == "active"
            )
        ).scalar()
        
        return {
            'total_plans': total or 0,
            'active_plans': active or 0,
            'inactive_plans': (total or 0) - (active or 0),
            'processing_completed': processing_completed or 0
        }

health_plan_crud = CRUDHealthPlan(HealthPlan)