"""
Query feedback schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    UNCLEAR = "unclear"

class FeedbackCreate(BaseModel):
    """Schema for creating query feedback"""
    query_id: str = Field(..., description="ID of the query being rated")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional feedback comment")
    suggested_improvement: Optional[str] = Field(None, max_length=1000, description="Suggested improvement")

class FeedbackOut(BaseModel):
    """Schema for feedback response"""
    id: str
    query_id: str
    feedback_type: FeedbackType
    rating: int
    comment: Optional[str]
    suggested_improvement: Optional[str]
    user_id: str
    tpa_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    total_feedback: int
    average_rating: float
    feedback_breakdown: dict  # {feedback_type: count}
    recent_feedback: list  # List of recent feedback items