"""
Chat endpoints for customer service agents
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatQueryRequest, ChatQueryResponse, ConversationCreate, 
    ConversationOut, MessageOut, ConversationList
)
from app.services.rag_service import RAGService
from app.services.analytics_service import analytics_service
from app.crud.conversation import conversation_crud
from app.crud.message import message_crud

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize RAG service
rag_service = RAGService()

class ConnectionManager:
    """WebSocket connection manager for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@router.post("/query", response_model=ChatQueryResponse)
async def process_chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a chat query and return AI response"""
    
    try:
        # Validate user permissions
        if current_user.role not in ["cs_agent", "cs_manager", "tpa_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for chat queries"
            )
        
        # Get conversation context if conversation_id provided
        conversation_context = None
        if request.conversation_id:
            conversation = await conversation_crud.get(
                db=db, id=request.conversation_id, tpa_id=current_user.tpa_id
            )
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Get recent messages for context
            recent_messages = await message_crud.get_recent_messages(
                db=db, conversation_id=request.conversation_id, limit=5
            )
            
            conversation_context = {
                "conversation_id": request.conversation_id,
                "member_id": conversation.member_id,
                "previous_queries": [
                    f"Q: {msg.content}" if msg.message_type == "user" 
                    else f"A: {msg.content}" 
                    for msg in recent_messages
                ]
            }
        
        # Process query with RAG service
        rag_response = await rag_service.process_query(
            db=db,
            query=request.query,
            tpa_id=current_user.tpa_id,
            health_plan_id=request.health_plan_id,
            conversation_context=conversation_context
        )
        
        # Track query analytics
        query_analytics_id = await analytics_service.track_query(
            db=db,
            query_text=request.query,
            response_data=rag_response,
            tpa_id=current_user.tpa_id,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            health_plan_name=request.health_plan_id,  # You might want to resolve this to actual name
            user_role=current_user.role
        )
        
        # Create or update conversation if needed
        if request.conversation_id or request.member_id:
            conversation_id = request.conversation_id
            
            # Create new conversation if member_id provided but no conversation_id
            if not conversation_id and request.member_id:
                conversation_data = ConversationCreate(
                    member_id=request.member_id,
                    agent_id=current_user.id,
                    health_plan_id=request.health_plan_id,
                    status="active",
                    title=request.query[:100] + "..." if len(request.query) > 100 else request.query
                )
                conversation = await conversation_crud.create(
                    db=db, obj_in=conversation_data, tpa_id=current_user.tpa_id
                )
                conversation_id = conversation.id
            
            # Save user message
            if conversation_id:
                await message_crud.create(
                    db=db,
                    obj_in={
                        "conversation_id": conversation_id,
                        "content": request.query,
                        "message_type": "user",
                        "sender_id": current_user.id
                    },
                    tpa_id=current_user.tpa_id
                )
                
                # Save AI response
                await message_crud.create(
                    db=db,
                    obj_in={
                        "conversation_id": conversation_id,
                        "content": rag_response["answer"],
                        "message_type": "assistant",
                        "metadata": {
                            "confidence_score": rag_response["confidence_score"],
                            "query_intent": rag_response["query_intent"],
                            "source_documents": rag_response["source_documents"],
                            "processing_time": rag_response["processing_time"]
                        }
                    },
                    tpa_id=current_user.tpa_id
                )
        
        # Prepare response
        response = ChatQueryResponse(
            answer=rag_response["answer"],
            confidence_score=rag_response["confidence_score"],
            query_intent=rag_response["query_intent"],
            source_documents=rag_response["source_documents"],
            related_topics=rag_response.get("related_topics", []),
            follow_up_suggestions=rag_response.get("follow_up_suggestions", []),
            processing_time=rag_response["processing_time"],
            conversation_id=conversation_id if 'conversation_id' in locals() else None,
            query_analytics_id=query_analytics_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat query processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat query: {str(e)}"
        )

@router.get("/suggestions")
async def get_query_suggestions(
    health_plan_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get common query suggestions"""
    
    try:
        suggestions = await rag_service.get_query_suggestions(
            db=db,
            tpa_id=current_user.tpa_id,
            health_plan_id=health_plan_id,
            limit=limit
        )
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Failed to get query suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get query suggestions"
        )

@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    
    try:
        # Set agent_id to current user if not provided
        if not conversation.agent_id:
            conversation.agent_id = current_user.id
        
        created_conversation = await conversation_crud.create(
            db=db, obj_in=conversation, tpa_id=current_user.tpa_id
        )
        
        return created_conversation
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation"
        )

@router.get("/conversations", response_model=ConversationList)
async def get_conversations(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    member_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversations for the current user's TPA"""
    
    try:
        # CS agents can only see their own conversations
        agent_id = current_user.id if current_user.role == "cs_agent" else None
        
        conversations = await conversation_crud.get_conversations(
            db=db,
            tpa_id=current_user.tpa_id,
            agent_id=agent_id,
            status=status,
            member_id=member_id,
            skip=skip,
            limit=limit
        )
        
        total = await conversation_crud.count_conversations(
            db=db,
            tpa_id=current_user.tpa_id,
            agent_id=agent_id,
            status=status,
            member_id=member_id
        )
        
        return ConversationList(
            conversations=conversations,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get conversations"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation with messages"""
    
    try:
        conversation = await conversation_crud.get(
            db=db, id=conversation_id, tpa_id=current_user.tpa_id
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check permissions - CS agents can only access their own conversations
        if (current_user.role == "cs_agent" and 
            conversation.agent_id != current_user.id):
            raise HTTPException(
                status_code=403, 
                detail="Access denied to this conversation"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get conversation"
        )

@router.put("/conversations/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation status (active, resolved, escalated)"""
    
    try:
        conversation = await conversation_crud.get(
            db=db, id=conversation_id, tpa_id=current_user.tpa_id
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check permissions
        if (current_user.role == "cs_agent" and 
            conversation.agent_id != current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Access denied to this conversation"
            )
        
        updated_conversation = await conversation_crud.update(
            db=db,
            db_obj=conversation,
            obj_in={"status": status, "updated_at": datetime.utcnow()}
        )
        
        return {"message": "Conversation status updated", "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update conversation status"
        )

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    
    try:
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connected for user: {user_id}")
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo message back or process as needed
            response = {
                "type": "message_received",
                "data": message_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_personal_message(response, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)