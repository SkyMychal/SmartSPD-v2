"""
Analytics schemas for request/response validation
"""
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# Query Analytics Schemas
class QueryAnalyticsBase(BaseModel):
    """Base schema for query analytics"""
    query_text: str = Field(..., max_length=1000)
    query_hash: Optional[str] = Field(None, max_length=64)
    query_intent: Optional[str] = Field(None, max_length=100)
    query_complexity: Optional[str] = Field(None, max_length=50)
    response_time: Decimal = Field(..., ge=0)
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    token_count: Optional[int] = Field(None, ge=0)
    documents_retrieved: Optional[int] = Field(None, ge=0)
    sources_cited: Optional[int] = Field(None, ge=0)
    health_plan_name: Optional[str] = Field(None, max_length=255)
    user_role: Optional[str] = Field(None, max_length=50)
    session_info: Optional[Dict[str, Any]] = None


class QueryAnalyticsCreate(QueryAnalyticsBase):
    """Schema for creating query analytics"""
    tpa_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class QueryAnalyticsUpdate(BaseModel):
    """Schema for updating query analytics"""
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    was_helpful: Optional[bool] = None
    feedback_text: Optional[str] = Field(None, max_length=500)


class QueryAnalytics(QueryAnalyticsBase):
    """Schema for query analytics response"""
    id: str
    tpa_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_rating: Optional[int] = None
    was_helpful: Optional[bool] = None
    feedback_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Activity Schemas  
class UserActivityBase(BaseModel):
    """Base schema for user activity"""
    activity_date: date
    queries_count: int = Field(default=0, ge=0)
    conversations_count: int = Field(default=0, ge=0)
    documents_accessed: int = Field(default=0, ge=0)
    active_time_minutes: int = Field(default=0, ge=0)
    avg_response_time: Optional[Decimal] = Field(None, ge=0)
    avg_confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    success_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    avg_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    positive_feedback_count: int = Field(default=0, ge=0)
    negative_feedback_count: int = Field(default=0, ge=0)


class UserActivityCreate(UserActivityBase):
    """Schema for creating user activity"""
    tpa_id: str
    user_id: str


class UserActivityUpdate(BaseModel):
    """Schema for updating user activity"""
    queries_count: Optional[int] = Field(None, ge=0)
    conversations_count: Optional[int] = Field(None, ge=0)
    documents_accessed: Optional[int] = Field(None, ge=0)
    active_time_minutes: Optional[int] = Field(None, ge=0)
    avg_response_time: Optional[Decimal] = Field(None, ge=0)
    avg_confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    success_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    avg_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    positive_feedback_count: Optional[int] = Field(None, ge=0)
    negative_feedback_count: Optional[int] = Field(None, ge=0)


class UserActivity(UserActivityBase):
    """Schema for user activity response"""
    id: str
    tpa_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Analytics Response Schemas
class PerformanceStats(BaseModel):
    """Performance statistics response"""
    total_queries: int
    avg_response_time: float
    avg_confidence_score: float
    avg_rating: float
    success_rate: float
    positive_feedback_rate: float


class QueryTrend(BaseModel):
    """Query trend data point"""
    date: str
    query_count: int
    avg_response_time: float
    avg_confidence: float


class ActivitySummary(BaseModel):
    """User activity summary response"""
    active_users: int
    total_queries: int
    total_conversations: int
    total_documents: int
    total_active_hours: float
    avg_response_time: float
    avg_success_rate: float


class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    active_conversations: int
    documents_processed: int
    active_users: int
    avg_response_time: str
    total_queries_today: int
    success_rate: float
    user_satisfaction: float
    recent_activity: List[Dict[str, Any]]


class AnalyticsResponse(BaseModel):
    """Complete analytics response"""
    performance_stats: PerformanceStats
    query_trends: List[QueryTrend]
    activity_summary: ActivitySummary
    dashboard_stats: DashboardStats


# Feedback Schemas
class QueryFeedback(BaseModel):
    """Schema for query feedback"""
    query_id: str
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    was_helpful: Optional[bool] = None
    feedback_text: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Response for feedback submission"""
    success: bool
    message: str
    query_id: str