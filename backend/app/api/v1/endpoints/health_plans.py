"""
Health plan management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

from app.core.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.models.health_plan import HealthPlan
from app.schemas.health_plan import HealthPlanOut, HealthPlanList, HealthPlanCreate, HealthPlanUpdate
from app.crud.health_plan import health_plan_crud
from app.services.audit_service import AuditService

router = APIRouter()

@router.get("/", response_model=HealthPlanList)
async def list_health_plans(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List health plans for the current user's TPA"""
    
    query = db.query(HealthPlan).filter(HealthPlan.tpa_id == current_user.tpa_id)
    
    if active_only:
        query = query.filter(HealthPlan.is_active == True)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    health_plans = query.offset(skip).limit(limit).all()
    
    return {
        "health_plans": health_plans,
        "total": total,
        "page": skip // limit + 1,
        "size": limit
    }

@router.get("/{health_plan_id}", response_model=HealthPlanOut)
async def get_health_plan(
    health_plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health plan details"""
    
    health_plan = db.query(HealthPlan).filter(
        HealthPlan.id == health_plan_id,
        HealthPlan.tpa_id == current_user.tpa_id
    ).first()
    
    if not health_plan:
        raise HTTPException(status_code=404, detail="Health plan not found")
    
    return health_plan

@router.post("/", response_model=HealthPlanOut)
async def create_health_plan(
    health_plan_in: HealthPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new health plan (Admin only)"""
    
    # Check if plan number already exists for this TPA
    existing_plan = await health_plan_crud.get_by_plan_number(
        db, plan_number=health_plan_in.plan_number, tpa_id=current_user.tpa_id
    )
    
    if existing_plan:
        raise HTTPException(
            status_code=400, 
            detail=f"Health plan with plan number '{health_plan_in.plan_number}' already exists"
        )
    
    # Create health plan with TPA association
    health_plan_data = health_plan_in.dict()
    health_plan_data["tpa_id"] = current_user.tpa_id
    
    health_plan = await health_plan_crud.create(db, obj_in=health_plan_data)
    
    # Audit log the creation
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="CREATE",
        resource_type="health_plan",
        resource_id=health_plan.id,
        description=f"Created health plan '{health_plan.name}' (Plan #: {health_plan.plan_number})",
        metadata={
            "plan_name": health_plan.name,
            "plan_number": health_plan.plan_number,
            "plan_year": health_plan.plan_year
        }
    )
    
    return health_plan

@router.put("/{health_plan_id}", response_model=HealthPlanOut)
async def update_health_plan(
    health_plan_id: str,
    health_plan_update: HealthPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update health plan details (Admin only)"""
    
    # Get existing health plan
    health_plan = db.query(HealthPlan).filter(
        HealthPlan.id == health_plan_id,
        HealthPlan.tpa_id == current_user.tpa_id
    ).first()
    
    if not health_plan:
        raise HTTPException(status_code=404, detail="Health plan not found")
    
    # Check for plan number conflicts if plan number is being updated
    if health_plan_update.plan_number and health_plan_update.plan_number != health_plan.plan_number:
        existing_plan = await health_plan_crud.get_by_plan_number(
            db, plan_number=health_plan_update.plan_number, tpa_id=current_user.tpa_id
        )
        
        if existing_plan and existing_plan.id != health_plan_id:
            raise HTTPException(
                status_code=400,
                detail=f"Health plan with plan number '{health_plan_update.plan_number}' already exists"
            )
    
    # Store original values for audit
    original_name = health_plan.name
    original_plan_number = health_plan.plan_number
    
    # Update health plan
    updated_health_plan = await health_plan_crud.update(
        db, db_obj=health_plan, obj_in=health_plan_update
    )
    
    # Audit log the update
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="UPDATE",
        resource_type="health_plan",
        resource_id=health_plan.id,
        description=f"Updated health plan '{updated_health_plan.name}'",
        metadata={
            "original_name": original_name,
            "original_plan_number": original_plan_number,
            "updated_name": updated_health_plan.name,
            "updated_plan_number": updated_health_plan.plan_number,
            "plan_year": updated_health_plan.plan_year
        }
    )
    
    return updated_health_plan

@router.delete("/{health_plan_id}")
async def delete_health_plan(
    health_plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete health plan (Admin only)"""
    
    # Get existing health plan
    health_plan = db.query(HealthPlan).filter(
        HealthPlan.id == health_plan_id,
        HealthPlan.tpa_id == current_user.tpa_id
    ).first()
    
    if not health_plan:
        raise HTTPException(status_code=404, detail="Health plan not found")
    
    # Check if health plan has associated documents
    document_count = len(health_plan.documents)
    
    if document_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete health plan with {document_count} associated documents. Remove documents first."
        )
    
    # Store details for audit before deletion
    plan_name = health_plan.name
    plan_number = health_plan.plan_number
    
    # Delete health plan
    await health_plan_crud.remove(db, id=health_plan_id)
    
    # Audit log the deletion
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="DELETE",
        resource_type="health_plan",
        resource_id=health_plan_id,
        description=f"Deleted health plan '{plan_name}' (Plan #: {plan_number})",
        metadata={
            "deleted_plan_name": plan_name,
            "deleted_plan_number": plan_number,
            "document_count_at_deletion": document_count
        }
    )
    
    return {"message": "Health plan deleted successfully"}

@router.get("/{health_plan_id}/documents")
async def get_health_plan_documents(
    health_plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents associated with a health plan"""
    
    health_plan = db.query(HealthPlan).filter(
        HealthPlan.id == health_plan_id,
        HealthPlan.tpa_id == current_user.tpa_id
    ).first()
    
    if not health_plan:
        raise HTTPException(status_code=404, detail="Health plan not found")
    
    # Return associated documents
    documents = [{
        "id": doc.id,
        "filename": doc.filename,
        "document_type": doc.document_type.value,
        "processing_status": doc.processing_status.value,
        "uploaded_at": doc.created_at,
        "file_size": doc.file_size,
        "page_count": doc.page_count
    } for doc in health_plan.documents]
    
    return {
        "health_plan_id": health_plan_id,
        "health_plan_name": health_plan.name,
        "document_count": len(documents),
        "documents": documents
    }