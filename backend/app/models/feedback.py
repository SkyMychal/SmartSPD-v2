"""
Query feedback model
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
import enum

class FeedbackType(enum.Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    UNCLEAR = "unclear"

class QueryFeedback(BaseModel):
    """Query feedback model for improving RAG responses"""
    __tablename__ = "query_feedback"
    
    # Feedback details
    query_id = Column(String(255), nullable=False, index=True)  # Reference to the original query
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 star rating
    comment = Column(Text)  # Optional user comment
    suggested_improvement = Column(Text)  # Suggested improvement
    
    # Query context (for analysis)
    original_query = Column(Text)  # Store the original query text
    original_response = Column(Text)  # Store the original response
    response_confidence = Column(Integer)  # Original confidence score
    
    # User and tenant info
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    tpa = relationship("TPA")
    
    def __repr__(self):
        return f"<QueryFeedback(query_id='{self.query_id}', type='{self.feedback_type}', rating={self.rating})>"