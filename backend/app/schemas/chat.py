"""
Chat schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatQueryRequest(BaseModel):
    """Request schema for chat queries"""
    query: str = Field(..., description="The user's question or query")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    member_id: Optional[str] = Field(None, description="Member ID for new conversations")
    health_plan_id: Optional[str] = Field(None, description="Health plan ID for context")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ChatQueryResponse(BaseModel):
    """Response schema for chat queries"""
    answer: str = Field(..., description="AI-generated response")
    confidence_score: float = Field(..., description="Confidence level (0-1)")
    query_intent: str = Field(..., description="Detected query intent")
    source_documents: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Source documents used for the response"
    )
    related_topics: List[str] = Field(
        default_factory=list,
        description="Related topics for further exploration"
    )
    follow_up_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    processing_time: float = Field(..., description="Processing time in seconds")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    query_analytics_id: Optional[str] = Field(None, description="Analytics ID for feedback tracking")

class ConversationCreate(BaseModel):
    """Schema for creating new conversations"""
    member_id: str = Field(..., description="Member ID")
    agent_id: Optional[str] = Field(None, description="Agent ID (auto-assigned if not provided)")
    health_plan_id: Optional[str] = Field(None, description="Health plan ID")
    title: str = Field(..., description="Conversation title")
    status: str = Field(default="active", description="Conversation status")
    priority: str = Field(default="normal", description="Priority level")
    tags: Optional[List[str]] = Field(default_factory=list, description="Conversation tags")

class ConversationUpdate(BaseModel):
    """Schema for updating conversations"""
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    agent_id: Optional[str] = None

class MessageOut(BaseModel):
    """Schema for message output"""
    id: str
    conversation_id: str
    content: str
    message_type: str  # 'user', 'assistant', 'system'
    sender_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    """Schema for conversation output"""
    id: str
    member_id: str
    agent_id: Optional[str] = None
    health_plan_id: Optional[str] = None
    title: str
    status: str
    priority: str
    tags: List[str] = Field(default_factory=list)
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Include recent messages
    messages: List[MessageOut] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    """Schema for conversation list response"""
    conversations: List[ConversationOut]
    total: int
    page: int
    size: int

class ChatMetrics(BaseModel):
    """Schema for chat metrics"""
    total_conversations: int
    active_conversations: int
    resolved_conversations: int
    average_response_time: float
    total_messages: int
    agent_performance: Dict[str, Any]

class QuerySuggestion(BaseModel):
    """Schema for query suggestions"""
    text: str
    category: str
    usage_count: int = 0

class ChatHealthCheck(BaseModel):
    """Schema for chat service health check"""
    status: str
    rag_service: Dict[str, Any]
    websocket_connections: int
    active_conversations: int