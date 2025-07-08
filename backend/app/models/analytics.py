"""
Analytics models for tracking usage and performance
"""
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Numeric, Date, Boolean
from sqlalchemy.orm import relationship
from .base import TenantModel

class QueryAnalytics(TenantModel):
    """Analytics for query performance and usage"""
    __tablename__ = "query_analytics"
    
    # Query info
    query_text = Column(String(1000), nullable=False)
    query_hash = Column(String(64), index=True)  # For deduplication
    query_intent = Column(String(100))
    query_complexity = Column(String(50))
    
    # Performance metrics
    response_time = Column(Numeric(10, 3), nullable=False)  # Response time in seconds
    confidence_score = Column(Numeric(5, 4))  # AI confidence
    token_count = Column(Integer)  # Token usage
    
    # Results
    documents_retrieved = Column(Integer)  # Number of chunks retrieved
    sources_cited = Column(Integer)  # Number of sources in response
    
    # User feedback
    user_rating = Column(Integer)  # 1-5 rating
    was_helpful = Column(Boolean)
    feedback_text = Column(String(500))
    
    # Context
    health_plan_name = Column(String(255))
    user_role = Column(String(50))
    session_info = Column(JSON)
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    
    def __repr__(self):
        return f"<QueryAnalytics(query_hash='{self.query_hash}', response_time='{self.response_time}')>"

class UserActivity(TenantModel):
    """Daily user activity tracking"""
    __tablename__ = "user_activity"
    
    # Activity date
    activity_date = Column(Date, nullable=False, index=True)
    
    # Usage metrics
    queries_count = Column(Integer, default=0)
    conversations_count = Column(Integer, default=0)
    documents_accessed = Column(Integer, default=0)
    active_time_minutes = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Numeric(10, 3))
    avg_confidence_score = Column(Numeric(5, 4))
    success_rate = Column(Numeric(5, 4))  # Percentage of successful queries
    
    # User satisfaction
    avg_rating = Column(Numeric(3, 2))  # Average user rating for the day
    positive_feedback_count = Column(Integer, default=0)
    negative_feedback_count = Column(Integer, default=0)
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserActivity(user_id='{self.user_id}', date='{self.activity_date}')>"