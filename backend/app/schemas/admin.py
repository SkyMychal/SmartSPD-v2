"""
Admin panel schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class AdminStats(BaseModel):
    """Overall admin dashboard statistics"""
    total_tpas: int
    active_tpas: int
    total_users: int
    active_users: int
    total_documents: int
    total_conversations: int
    recent_users_30d: int
    recent_documents_30d: int
    recent_conversations_30d: int
    last_updated: datetime

class TPAOverview(BaseModel):
    """TPA overview for admin metrics"""
    id: str
    name: str
    slug: str
    user_count: int
    document_count: int
    conversation_count: int
    is_active: bool
    created_at: datetime

class SystemMetrics(BaseModel):
    """Detailed system performance metrics"""
    tpa_overview: List[TPAOverview]
    avg_query_response_time: float
    avg_document_processing_time: float
    system_uptime_hours: float
    memory_usage_mb: float
    cpu_usage_percent: float

class UserActivitySummary(BaseModel):
    """User activity summary for admin dashboard"""
    user_id: str
    user_name: str
    email: str
    tpa_id: str
    tpa_name: str
    last_login: Optional[datetime]
    login_count: int
    conversation_count: int
    document_count: int
    is_active: bool

class RecentActivity(BaseModel):
    """Recent system activity item"""
    type: str  # user_created, document_uploaded, conversation_started, etc.
    description: str
    timestamp: datetime
    user_id: Optional[str] = None
    tpa_id: Optional[str] = None

class AdminDashboardData(BaseModel):
    """Complete admin dashboard data"""
    stats: AdminStats
    metrics: SystemMetrics
    recent_activity: List[RecentActivity]
    
class BulkUserAction(BaseModel):
    """Bulk action on users"""
    user_ids: List[str]
    action: str  # activate, deactivate, delete
    
class BulkUserActionResult(BaseModel):
    """Result of bulk user action"""
    success_count: int
    failed_count: int
    errors: List[str]
    
class SystemHealthCheck(BaseModel):
    """System health check status"""
    database_status: str
    redis_status: str
    neo4j_status: str
    vector_db_status: str
    ai_service_status: str
    overall_status: str
    last_check: datetime

class AdminAuditLog(BaseModel):
    """Admin action audit log entry"""
    id: str
    admin_user_id: str
    admin_user_name: str
    action: str
    target_type: str  # user, tpa, document, etc.
    target_id: str
    details: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None