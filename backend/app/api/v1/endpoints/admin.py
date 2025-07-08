"""
Admin dashboard endpoints for system administration
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin
from app.crud import tpa_crud, user_crud, conversation_crud, document_crud
from app.models.user import User
from app.schemas.tpa import TPAOut, TPACreate, TPAUpdate
from app.schemas.user import UserOut as UserSchema, UserCreate, UserUpdate
from app.schemas.admin import (
    AdminStats, 
    SystemMetrics, 
    UserActivitySummary,
    TPAOverview
)
from app.services.audit_service import AuditService
from app.core.audit import audit_admin, audit_endpoint

router = APIRouter()

@router.get("/stats", response_model=AdminStats)
@audit_endpoint(action="get_admin_stats", resource_type="system", severity="low")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive admin dashboard statistics"""
    
    # Get total counts
    total_tpas = len(await tpa_crud.get_multi(db))
    active_tpas = len(await tpa_crud.get_active(db))
    
    # Get user statistics across all TPAOuts
    all_users = await user_crud.get_multi(db)
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.is_active])
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = len([u for u in all_users if u.created_at >= thirty_days_ago])
    
    # Get document statistics
    all_documents = await document_crud.get_multi(db)
    total_documents = len(all_documents)
    recent_documents = len([d for d in all_documents if d.created_at >= thirty_days_ago])
    
    # Get conversation statistics
    all_conversations = await conversation_crud.get_multi(db)
    total_conversations = len(all_conversations)
    recent_conversations = len([c for c in all_conversations if c.created_at >= thirty_days_ago])
    
    return AdminStats(
        total_tpas=total_tpas,
        active_tpas=active_tpas,
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_conversations=total_conversations,
        recent_users_30d=recent_users,
        recent_documents_30d=recent_documents,
        recent_conversations_30d=recent_conversations,
        last_updated=datetime.utcnow()
    )

@router.get("/metrics", response_model=SystemMetrics)
@audit_endpoint(action="get_system_metrics", resource_type="system", severity="low")
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get detailed system performance metrics"""
    
    # Calculate metrics by TPAOut
    tpas = await tpa_crud.get_multi(db)
    tpa_metrics = []
    
    for tpa in tpas:
        user_count = await user_crud.get_active_users_count(db, tpa_id=tpa.id)
        documents = await document_crud.get_by_tpa(db, tpa_id=tpa.id)
        conversations = await conversation_crud.get_by_tpa(db, tpa_id=tpa.id)
        
        tpa_metrics.append(TPAOverview(
            id=tpa.id,
            name=tpa.name,
            slug=tpa.slug,
            user_count=user_count,
            document_count=len(documents),
            conversation_count=len(conversations),
            is_active=tpa.is_active,
            created_at=tpa.created_at
        ))
    
    # Calculate average response times (placeholder for actual metrics)
    avg_query_time = 1.2  # Would come from analytics service
    avg_processing_time = 3.5  # Would come from document processor
    
    return SystemMetrics(
        tpa_overview=tpa_metrics,
        avg_query_response_time=avg_query_time,
        avg_document_processing_time=avg_processing_time,
        system_uptime_hours=168,  # Placeholder
        memory_usage_mb=512,  # Placeholder
        cpu_usage_percent=45.2  # Placeholder
    )

@router.get("/users", response_model=List[UserSchema])
@audit_endpoint(action="get_all_users", resource_type="user", severity="low")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    tpa_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all users with filtering options"""
    
    if search and tpa_id:
        # Search within specific TPAOut
        users = await user_crud.search_users(
            db, tpa_id=tpa_id, query=search, skip=skip, limit=limit
        )
    elif tpa_id:
        # Get users for specific TPAOut
        users = await user_crud.get_by_tpa(db, tpa_id=tpa_id, skip=skip, limit=limit)
    else:
        # Get all users
        users = await user_crud.get_multi(db, skip=skip, limit=limit)
    
    # Apply active filter if specified
    if is_active is not None:
        users = [u for u in users if u.is_active == is_active]
    
    return users

@router.post("/users", response_model=UserSchema)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user"""
    
    # Check if user already exists
    existing_user = await user_crud.get_by_email_and_tpa(
        db, email=user_in.email, tpa_id=user_in.tpa_id
    )
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists in this TPAOut"
        )
    
    # Verify TPAOut exists
    tpa = await tpa_crud.get(db, id=user_in.tpa_id)
    if not tpa:
        raise HTTPException(status_code=404, detail="TPA not found")
    
    user = await user_crud.create(db, obj_in=user_in)
    
    # Log admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="user_create",
        description=f"Created user {user.email} in TPAOut {tpa.name}",
        resource_type="user",
        resource_id=user.id,
        new_values={
            "email": user.email,
            "role": user.role,
            "tpa_id": user.tpa_id
        }
    )
    
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a user"""
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_values = {
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    
    user = await user_crud.update(db, db_obj=user, obj_in=user_in)
    
    # Log admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="user_update",
        description=f"Updated user {user.email}",
        resource_type="user",
        resource_id=user.id,
        old_values=old_values,
        new_values={
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    )
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a user"""
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log admin action before deletion
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="user_delete",
        description=f"Deleted user {user.email}",
        resource_type="user",
        resource_id=user.id,
        old_values={
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
    )
    
    await user_crud.remove(db, id=user_id)
    return {"message": "User deleted successfully"}

@router.get("/tpas", response_model=List[TPAOut])
@audit_endpoint(action="get_tpas", resource_type="tpa", severity="low")
async def get_tpas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all TPAOuts"""
    
    if active_only:
        tpas = await tpa_crud.get_active(db)
    else:
        tpas = await tpa_crud.get_multi(db, skip=skip, limit=limit)
    
    return tpas

@router.post("/tpas", response_model=TPAOut)
async def create_tpa(
    tpa_in: TPACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new TPAOut"""
    
    # Check if TPAOut with same name or slug already exists
    existing_tpa = await tpa_crud.get_by_slug(db, slug=tpa_in.slug or "")
    if existing_tpa and tpa_in.slug:
        raise HTTPException(
            status_code=400,
            detail="TPA with this slug already exists"
        )
    
    tpa = await tpa_crud.create_with_slug(db, obj_in=tpa_in)
    
    # Log admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="tpa_create",
        description=f"Created TPAOut {tpa.name}",
        resource_type="tpa",
        resource_id=tpa.id,
        new_values={
            "name": tpa.name,
            "slug": tpa.slug,
            "is_active": tpa.is_active
        }
    )
    
    return tpa

@router.put("/tpas/{tpa_id}", response_model=TPAOut)
async def update_tpa(
    tpa_id: str,
    tpa_in: TPAUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a TPAOut"""
    
    tpa = await tpa_crud.get(db, id=tpa_id)
    if not tpa:
        raise HTTPException(status_code=404, detail="TPA not found")
    
    old_values = {
        "name": tpa.name,
        "slug": tpa.slug,
        "is_active": tpa.is_active,
        "description": getattr(tpa, 'description', None)
    }
    
    tpa = await tpa_crud.update(db, db_obj=tpa, obj_in=tpa_in)
    
    # Log admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="tpa_update",
        description=f"Updated TPAOut {tpa.name}",
        resource_type="tpa",
        resource_id=tpa.id,
        old_values=old_values,
        new_values={
            "name": tpa.name,
            "slug": tpa.slug,
            "is_active": tpa.is_active,
            "description": getattr(tpa, 'description', None)
        }
    )
    
    return tpa

@router.delete("/tpas/{tpa_id}")
async def delete_tpa(
    tpa_id: str,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a TPAOut"""
    
    tpa = await tpa_crud.get(db, id=tpa_id)
    if not tpa:
        raise HTTPException(status_code=404, detail="TPA not found")
    
    # Check if TPAOut has users
    if not force:
        user_count = await user_crud.get_active_users_count(db, tpa_id=tpa_id)
        if user_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete TPAOut with {user_count} active users. Use force=true to delete anyway."
            )
    
    # Log admin action before deletion
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="tpa_delete",
        description=f"Deleted TPAOut {tpa.name} (forced: {force})",
        resource_type="tpa",
        resource_id=tpa.id,
        old_values={
            "name": tpa.name,
            "slug": tpa.slug,
            "is_active": tpa.is_active
        }
    )
    
    await tpa_crud.remove(db, id=tpa_id)
    return {"message": "TPA deleted successfully"}

@router.get("/activity", response_model=List[UserActivitySummary])
@audit_endpoint(action="get_recent_activity", resource_type="system", severity="low")
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get recent system activity"""
    
    since_date = datetime.utcnow() - timedelta(days=days)
    activities = []
    
    # Get recent users
    recent_users = [u for u in await user_crud.get_multi(db) if u.created_at >= since_date]
    for user in recent_users[-10:]:  # Last 10
        activities.append(UserActivitySummary(
            type="user_created",
            description=f"New user registered: {user.first_name} {user.last_name}",
            timestamp=user.created_at,
            user_id=user.id,
            tpa_id=user.tpa_id
        ))
    
    # Get recent documents
    recent_docs = [d for d in await document_crud.get_multi(db) if d.created_at >= since_date]
    for doc in recent_docs[-10:]:  # Last 10
        activities.append(UserActivitySummary(
            type="document_uploaded",
            description=f"Document uploaded: {doc.filename}",
            timestamp=doc.created_at,
            user_id=doc.uploaded_by,
            tpa_id=doc.tpa_id
        ))
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset a user's password"""
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user_crud.update_password(db, user=user, new_password=new_password)
    
    # Log security-critical admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="password_reset",
        description=f"Reset password for user {user.email}",
        resource_type="user",
        resource_id=user.id
    )
    
    return {"message": "Password reset successfully"}

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Toggle user active/inactive status"""
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_update = UserUpdate(is_active=not user.is_active)
    old_status = user.is_active
    user = await user_crud.update(db, db_obj=user, obj_in=user_update)
    
    # Log admin action
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="user_status_toggle",
        description=f"{'Activated' if user.is_active else 'Deactivated'} user {user.email}",
        resource_type="user",
        resource_id=user.id,
        old_values={"is_active": old_status},
        new_values={"is_active": user.is_active}
    )
    
    status = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status} successfully", "is_active": user.is_active}