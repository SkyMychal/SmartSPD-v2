"""
Audit schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class AuditLogBase(BaseModel):
    """Base audit log schema"""
    tpa_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    severity: Optional[str] = "low"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    """Schema for creating audit logs"""
    pass

class AuditLogUpdate(BaseModel):
    """Schema for updating audit logs (limited fields)"""
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogResponse(AuditLogBase):
    """Schema for audit log responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AuditSummaryResponse(BaseModel):
    """Schema for audit summary statistics"""
    total_events: int
    failed_events: int
    failure_rate: float
    action_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    resource_breakdown: Dict[str, int]
    period_start: Optional[datetime]
    period_end: Optional[datetime]

class AuditQueryFilters(BaseModel):
    """Schema for audit query filters"""
    tpa_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None

class UserAuditSummary(BaseModel):
    """Schema for user-specific audit summary"""
    user_id: str
    user_name: str
    user_email: str
    total_actions: int
    login_count: int
    query_count: int
    document_actions: int
    failed_actions: int
    last_activity: Optional[datetime]
    most_common_action: Optional[str]
    
class SecurityAuditEvent(BaseModel):
    """Schema for security audit events"""
    event_type: str
    severity: str
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    risk_score: Optional[int] = None
    mitigation_applied: bool = False
    
class ComplianceReport(BaseModel):
    """Schema for compliance reporting"""
    report_id: str
    tpa_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    total_events: int
    security_events: int
    data_access_events: int
    admin_actions: int
    failed_operations: int
    compliance_score: float
    findings: List[str]
    recommendations: List[str]
    generated_at: datetime
    
class AuditTrailExport(BaseModel):
    """Schema for audit trail export"""
    export_format: str  # csv, json, xlsx
    filters: AuditQueryFilters
    include_metadata: bool = True
    include_user_details: bool = True
    
class AuditMetrics(BaseModel):
    """Schema for audit metrics and KPIs"""
    total_users_active: int
    total_queries_today: int
    total_documents_processed: int
    security_incidents_today: int
    failed_operations_rate: float
    top_actions: List[Dict[str, Any]]
    top_users_by_activity: List[Dict[str, Any]]
    hourly_activity: List[Dict[str, Any]]
    
class DataAccessLog(BaseModel):
    """Schema for data access logging"""
    user_id: str
    resource_type: str
    resource_id: str
    access_type: str  # read, write, delete
    data_classification: str  # public, internal, confidential, restricted
    purpose: str
    legal_basis: Optional[str] = None  # For GDPR compliance
    retention_period: Optional[int] = None  # Days
    
class PrivacyAuditEvent(BaseModel):
    """Schema for privacy-related audit events"""
    event_type: str  # data_access, data_export, data_deletion, consent_change
    subject_id: str  # Data subject identifier
    data_types: List[str]  # Types of personal data involved
    legal_basis: str
    purpose: str
    retention_period: Optional[int] = None
    consent_status: Optional[str] = None
    
class SystemAuditHealth(BaseModel):
    """Schema for system audit health check"""
    audit_system_status: str
    logs_processed_today: int
    logs_failed_today: int
    storage_usage_mb: float
    retention_compliance: bool
    backup_status: str
    last_cleanup: Optional[datetime]
    
class RiskAssessment(BaseModel):
    """Schema for risk assessment based on audit data"""
    risk_level: str  # low, medium, high, critical
    risk_score: int  # 0-100
    risk_factors: List[str]
    recommendations: List[str]
    auto_actions_taken: List[str]
    requires_manual_review: bool