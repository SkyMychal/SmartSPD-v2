"""
Audit service for compliance tracking
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.audit import AuditLog, AuditAction, AuditSeverity
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_event(
        db: Session,
        *,
        tpa_id: str,
        action: str,
        resource_type: str,
        description: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: str = "low",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log an audit event"""
        
        try:
            audit_log = AuditLog(
                tpa_id=tpa_id,
                user_id=user_id,
                action=AuditAction(action),
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                severity=AuditSeverity(severity),
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                request_method=request_method,
                old_values=old_values,
                new_values=new_values,
                metadata=metadata,
                success=success,
                error_message=error_message
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def log_auth_event(
        db: Session,
        *,
        user_id: str,
        tpa_id: str,
        action: str,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log authentication-related events"""
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action=action,
            resource_type="authentication",
            description=description or f"Authentication event: {action}",
            severity="medium" if not success else "low",
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    async def log_data_access(
        db: Session,
        *,
        user_id: str,
        tpa_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log data access events"""
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description or f"Data access: {resource_type}",
            severity="low",
            metadata=metadata
        )
    
    @staticmethod
    async def log_admin_action(
        db: Session,
        *,
        user_id: str,
        tpa_id: str,
        action: str,
        description: str,
        resource_type: str = "system",
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log administrative actions"""
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action="admin_action",
            resource_type=resource_type,
            resource_id=resource_id,
            description=f"Admin action: {description}",
            severity="high",
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    async def log_query_event(
        db: Session,
        *,
        user_id: str,
        tpa_id: str,
        query_text: str,
        health_plan_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        response_time: Optional[float] = None,
        confidence_score: Optional[float] = None,
        success: bool = True
    ) -> AuditLog:
        """Log query/chat events"""
        
        metadata = {
            "query_length": len(query_text),
            "health_plan_id": health_plan_id,
            "conversation_id": conversation_id,
            "response_time": response_time,
            "confidence_score": confidence_score
        }
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action="query",
            resource_type="conversation",
            resource_id=conversation_id,
            description=f"Query submitted: {query_text[:100]}{'...' if len(query_text) > 100 else ''}",
            severity="low",
            metadata=metadata,
            success=success
        )
    
    @staticmethod
    async def log_document_event(
        db: Session,
        *,
        user_id: str,
        tpa_id: str,
        action: str,
        document_id: str,
        filename: str,
        document_type: Optional[str] = None,
        file_size: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log document-related events"""
        
        metadata = {
            "filename": filename,
            "document_type": document_type,
            "file_size": file_size
        }
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action=action,
            resource_type="document",
            resource_id=document_id,
            description=f"Document {action}: {filename}",
            severity="medium" if action in ["delete", "update"] else "low",
            metadata=metadata,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    async def log_security_event(
        db: Session,
        *,
        tpa_id: str,
        action: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "high",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log security-related events"""
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id,
            user_id=user_id,
            action=action,
            resource_type="security",
            description=f"Security event: {description}",
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
    
    @staticmethod
    async def log_system_event(
        db: Session,
        *,
        action: str,
        description: str,
        tpa_id: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log system-level events"""
        
        return AuditService.log_event(
            db=db,
            tpa_id=tpa_id or "system",
            user_id=user_id,
            action=action,
            resource_type="system",
            description=f"System event: {description}",
            severity=severity,
            metadata=metadata,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    async def get_audit_logs(
        db: Session,
        *,
        tpa_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Retrieve audit logs with filtering"""
        
        from sqlalchemy import and_, or_
        
        query = db.query(AuditLog)
        
        filters = []
        if tpa_id:
            filters.append(AuditLog.tpa_id == tpa_id)
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if action:
            filters.append(AuditLog.action == action)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if severity:
            filters.append(AuditLog.severity == severity)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    async def get_audit_summary(
        db: Session,
        *,
        tpa_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit summary statistics"""
        
        from sqlalchemy import func, and_
        
        query = db.query(AuditLog)
        
        filters = []
        if tpa_id:
            filters.append(AuditLog.tpa_id == tpa_id)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Count by action
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(and_(*filters) if filters else True).group_by(AuditLog.action).all()
        
        # Count by severity
        severity_counts = db.query(
            AuditLog.severity,
            func.count(AuditLog.id).label('count')
        ).filter(and_(*filters) if filters else True).group_by(AuditLog.severity).all()
        
        # Count by resource type
        resource_counts = db.query(
            AuditLog.resource_type,
            func.count(AuditLog.id).label('count')
        ).filter(and_(*filters) if filters else True).group_by(AuditLog.resource_type).all()
        
        # Get failure rate
        total_events = query.count()
        failed_events = query.filter(AuditLog.success == False).count()
        failure_rate = (failed_events / total_events * 100) if total_events > 0 else 0
        
        return {
            "total_events": total_events,
            "failed_events": failed_events,
            "failure_rate": failure_rate,
            "action_breakdown": {action: count for action, count in action_counts},
            "severity_breakdown": {severity.value: count for severity, count in severity_counts},
            "resource_breakdown": {resource: count for resource, count in resource_counts},
            "period_start": start_date,
            "period_end": end_date
        }
    
    @staticmethod
    async def cleanup_old_logs(
        db: Session,
        *,
        retention_days: int = 90,
        batch_size: int = 1000
    ) -> int:
        """Clean up old audit logs beyond retention period"""
        
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete in batches to avoid long-running transactions
        total_deleted = 0
        while True:
            logs_to_delete = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).limit(batch_size).all()
            
            if not logs_to_delete:
                break
            
            for log in logs_to_delete:
                db.delete(log)
            
            db.commit()
            total_deleted += len(logs_to_delete)
            
            logger.info(f"Deleted {len(logs_to_delete)} audit logs, total: {total_deleted}")
        
        return total_deleted