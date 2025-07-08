"""
Conversation and Message models for chat functionality
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Enum, Numeric, Integer
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import TenantModel

class ConversationStatus(PyEnum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ARCHIVED = "archived"

class MessageType(PyEnum):
    """Message type enumeration"""
    USER_QUERY = "user_query"
    AI_RESPONSE = "ai_response"
    SYSTEM = "system"
    FEEDBACK = "feedback"

class Conversation(TenantModel):
    """Conversation model for chat sessions"""
    __tablename__ = "conversations"
    
    # Basic info
    title = Column(String(255))  # Auto-generated or user-defined
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    
    # Context
    session_id = Column(String(100), index=True)  # Browser session ID
    context = Column(JSON)  # Conversation context and state
    
    # Performance metrics
    total_messages = Column(Integer, default=0)
    avg_response_time = Column(Numeric(10, 3))  # Average response time in seconds
    satisfaction_rating = Column(Integer)  # 1-5 rating
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    health_plan_id = Column(String(36), ForeignKey("health_plans.id"))
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    health_plan = relationship("HealthPlan", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', user_id='{self.user_id}')>"

class Message(TenantModel):
    """Message model for individual chat messages"""
    __tablename__ = "messages"
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    
    # Metadata
    query_intent = Column(String(100))  # Classified intent
    query_complexity = Column(String(50))  # simple, medium, complex
    
    # AI response metadata
    confidence_score = Column(Numeric(5, 4))  # AI confidence (0-1)
    source_documents = Column(JSON)  # Referenced document chunks
    reasoning = Column(Text)  # AI reasoning/explanation
    
    # Performance tracking
    response_time = Column(Numeric(10, 3))  # Response time in seconds
    token_count = Column(Integer)  # Token usage for AI responses
    
    # User feedback
    user_rating = Column(Integer)  # 1-5 rating for this specific response
    user_feedback = Column(Text)   # Optional user feedback
    was_helpful = Column(Boolean)  # Thumbs up/down
    
    # Processing info
    model_used = Column(String(100))  # AI model used for response
    processing_log = Column(JSON)    # Debug information
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(type='{self.message_type.value}', conversation_id='{self.conversation_id}')>"