"""
Audit endpoints for compliance tracking
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin, require_manager
from app.services.audit_service import AuditService
from app.models.user import User
from app.schemas.audit import (
    AuditLogResponse,
    AuditSummaryResponse,
    AuditLogCreate,
    AuditQueryFilters
)

router = APIRouter()

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    tpa_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get audit logs with filtering options"""
    
    # Non-admin users can only see their own TPA's logs
    if current_user.role != "tpa_admin":
        tpa_id = current_user.tpa_id
    
    logs = await AuditService.get_audit_logs(
        db=db,
        tpa_id=tpa_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return logs

@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get audit summary statistics"""
    
    # Non-admin users can only see their own TPA's summary
    if current_user.role != "tpa_admin":
        tpa_id = current_user.tpa_id
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    summary = await AuditService.get_audit_summary(
        db=db,
        tpa_id=tpa_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return summary

@router.post("/log", response_model=AuditLogResponse)
async def create_audit_log(
    audit_data: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Manually create an audit log entry (admin only)"""
    
    log = await AuditService.log_event(
        db=db,
        tpa_id=audit_data.tpa_id,
        user_id=audit_data.user_id,
        action=audit_data.action,
        resource_type=audit_data.resource_type,
        resource_id=audit_data.resource_id,
        description=audit_data.description,
        severity=audit_data.severity or "low",
        metadata=audit_data.metadata,
        success=audit_data.success
    )
    
    return log

@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
async def get_user_audit_logs(
    user_id: str,
    days: int = Query(30, ge=1, le=90),
    action: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get audit logs for a specific user"""
    
    # Non-admin users can only see logs for users in their TPA
    tpa_id = None if current_user.role == "tpa_admin" else current_user.tpa_id
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logs = await AuditService.get_audit_logs(
        db=db,
        tpa_id=tpa_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return logs

@router.get("/security", response_model=List[AuditLogResponse])
async def get_security_audit_logs(
    days: int = Query(7, ge=1, le=30),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get security-related audit logs (admin only)"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logs = await AuditService.get_audit_logs(
        db=db,
        resource_type="security",
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return logs

@router.get("/failed", response_model=List[AuditLogResponse])
async def get_failed_audit_logs(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    resource_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get failed operations audit logs"""
    
    # Non-admin users can only see their own TPA's logs
    if current_user.role != "tpa_admin":
        tpa_id = current_user.tpa_id
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Filter to only failed operations
    from app.models.audit import AuditLog
    from sqlalchemy import and_
    
    query = db.query(AuditLog).filter(AuditLog.success == False)
    
    filters = []
    if tpa_id:
        filters.append(AuditLog.tpa_id == tpa_id)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if start_date:
        filters.append(AuditLog.created_at >= start_date)
    if end_date:
        filters.append(AuditLog.created_at <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return logs

@router.post("/cleanup")
async def cleanup_old_audit_logs(
    retention_days: int = Query(90, ge=30, le=365),
    dry_run: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Clean up old audit logs (admin only)"""
    
    if dry_run:
        # Count how many would be deleted
        from datetime import timedelta
        from app.models.audit import AuditLog
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        count = db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).count()
        
        return {
            "message": f"Dry run: Would delete {count} audit logs older than {retention_days} days",
            "cutoff_date": cutoff_date,
            "records_to_delete": count
        }
    else:
        deleted_count = await AuditService.cleanup_old_logs(
            db=db,
            retention_days=retention_days
        )
        
        # Log the cleanup action
        await AuditService.log_admin_action(
            db=db,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            action="audit_cleanup",
            description=f"Cleaned up {deleted_count} audit logs older than {retention_days} days",
            resource_type="audit"
        )
        
        return {
            "message": f"Successfully deleted {deleted_count} audit logs",
            "deleted_count": deleted_count,
            "retention_days": retention_days
        }

@router.get("/actions", response_model=List[str])
async def get_audit_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get list of available audit actions"""
    
    from app.models.audit import AuditLog
    from sqlalchemy import distinct
    
    # Get distinct actions from the database
    actions = db.query(distinct(AuditLog.action)).all()
    action_list = [action[0] for action in actions if action[0]]
    
    # Add common actions that might not be in the database yet
    common_actions = [
        "login", "logout", "query", "upload", "download", "create", "update", 
        "delete", "admin_action", "security_event", "system_event"
    ]
    
    # Merge and deduplicate
    all_actions = list(set(action_list + common_actions))
    
    return sorted(all_actions)

@router.get("/resource-types", response_model=List[str])
async def get_audit_resource_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get list of available resource types"""
    
    from app.models.audit import AuditLog
    from sqlalchemy import distinct
    
    # Get distinct resource types from the database
    resources = db.query(distinct(AuditLog.resource_type)).all()
    resource_list = [resource[0] for resource in resources if resource[0]]
    
    # Add common resource types
    common_resources = [
        "user", "document", "conversation", "health_plan", "tpa", 
        "authentication", "security", "system", "audit"
    ]
    
    # Merge and deduplicate
    all_resources = list(set(resource_list + common_resources))
    
    return sorted(all_resources)