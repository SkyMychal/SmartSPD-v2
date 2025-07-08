"""
Audit logging for compliance and security
"""
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import TenantModel

class AuditAction(PyEnum):
    """Audit action enumeration"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    QUERY = "query"
    EXPORT = "export"
    ADMIN_ACTION = "admin_action"

class AuditSeverity(PyEnum):
    """Audit severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(TenantModel):
    """Audit log for compliance tracking"""
    __tablename__ = "audit_logs"
    
    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)  # user, document, health_plan, etc.
    resource_id = Column(String(36))  # ID of the affected resource
    
    # Context
    description = Column(Text, nullable=False)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.LOW, nullable=False)
    
    # Request details
    ip_address = Column(String(45))  # Supports IPv6
    user_agent = Column(String(500))
    request_path = Column(String(500))
    request_method = Column(String(10))
    
    # Data changes (for compliance)
    old_values = Column(JSON)  # Previous values for updates
    new_values = Column(JSON)  # New values for updates
    
    # Additional metadata
    audit_metadata = Column("metadata", JSON)  # Additional context-specific data
    
    # Status
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text)
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action.value}', resource_type='{self.resource_type}')>"