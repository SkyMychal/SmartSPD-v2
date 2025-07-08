"""
Chat/query endpoints with audit logging
"""
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import get_current_user_token, TokenData
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.analytics_service import AnalyticsService
from app.services.rag_service import RAGService
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.crud.document import document_crud

router = APIRouter()

# Initialize RAG service
rag_service = RAGService()
logger = logging.getLogger(__name__)

@router.post("/query", response_model=ChatQueryResponse)
async def submit_query(
    query_data: ChatQueryRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit chat query with comprehensive audit logging"""
    
    start_time = datetime.utcnow()
    
    try:
        # Validate query
        if not query_data.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Check if there are any processed documents available for querying
        has_processed_docs = await document_crud.has_processed_documents(
            db, tpa_id=current_user.tpa_id, health_plan_id=query_data.health_plan_id
        )
        
        if not has_processed_docs:
            # Get processing summary for informative error message
            processing_summary = await document_crud.get_processing_summary(
                db, tpa_id=current_user.tpa_id
            )
            
            if processing_summary['total_documents'] == 0:
                error_message = "No documents have been uploaded yet. Please upload health plan documents (SPD or BPS files) before submitting queries."
            elif processing_summary['processing'] > 0:
                error_message = f"Documents are still being processed ({processing_summary['processing']} in progress). Please wait for processing to complete before submitting queries."
            elif processing_summary['failed'] > 0 and processing_summary['completed'] == 0:
                error_message = "Document processing failed. Please check your uploaded documents or contact support."
            else:
                error_message = "No processed documents available for queries. Please upload and process health plan documents first."
            
            raise HTTPException(
                status_code=409,  # Conflict - resource not ready
                detail={
                    "message": error_message,
                    "processing_summary": processing_summary,
                    "ready_for_queries": False
                }
            )
        
        # Process query using enhanced RAG service
        try:
            # Get conversation context if available
            conversation_context = await _get_conversation_context(
                db, query_data.conversation_id, current_user.id
            ) if query_data.conversation_id else None
            
            rag_response = await rag_service.process_query(
                db=db,
                query=query_data.query,
                tpa_id=current_user.tpa_id,
                health_plan_id=query_data.health_plan_id,
                conversation_context=conversation_context
            )
            
            response = {
                "query_id": f"query_{int(datetime.utcnow().timestamp())}",
                "response": rag_response['answer'],
                "confidence_score": rag_response['confidence_score'],
                "sources": [
                    f"{source.get('chunk_type', 'Document')} (Score: {source['score']:.2f})"
                    for source in rag_response['source_documents'][:3]  # Top 3 sources
                ],
                "health_plan_id": query_data.health_plan_id,
                "conversation_id": query_data.conversation_id,
                "query_intent": rag_response.get('query_intent', 'general'),
                "related_topics": rag_response.get('related_topics', []),
                "follow_up_suggestions": rag_response.get('follow_up_suggestions', [])
            }
            
        except Exception as e:
            logger.error(f"RAG service failed: {e}")
            # Fallback response
            response = {
                "query_id": f"query_{int(datetime.utcnow().timestamp())}",
                "response": "I'm having trouble accessing the plan documents right now. Please try again later or contact customer service for assistance.",
                "confidence_score": 0.0,
                "sources": [],
                "health_plan_id": query_data.health_plan_id,
                "conversation_id": query_data.conversation_id,
                "error": "RAG service unavailable"
            }
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        # Log query for analytics
        try:
            await AnalyticsService.track_query(
                db=db,
                user_id=current_user.id,
                tpa_id=current_user.tpa_id,
                query_text=query_data.query,
                response_time=response_time,
                confidence_score=response.get("confidence_score"),
                health_plan_id=query_data.health_plan_id,
                conversation_id=query_data.conversation_id
            )
        except Exception as e:
            # Don't fail the request if analytics tracking fails
            pass
        
        # Audit log the query
        AuditService.log_query_event(
            db=db,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            query_text=query_data.query,
            health_plan_id=query_data.health_plan_id,
            conversation_id=query_data.conversation_id,
            response_time=response_time,
            confidence_score=response.get("confidence_score"),
            success=True
        )
        
        return response
        
    except Exception as e:
        # Log failed query
        AuditService.log_query_event(
            db=db,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            query_text=query_data.query,
            health_plan_id=query_data.health_plan_id,
            conversation_id=query_data.conversation_id,
            success=False
        )
        
        raise

@router.get("/conversations", response_model=List[dict])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's conversation history"""
    
    # Audit log data access
    AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="conversation",
        resource_id="list",
        action="read",
        description="Retrieved conversation history"
    )
    
    # Return placeholder data
    return [
        {
            "id": "conv_1",
            "title": "Benefits Inquiry",
            "updated_at": datetime.utcnow(),
            "message_count": 5
        }
    ]

@router.get("/suggestions", response_model=List[str])
async def get_query_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get query suggestions for the user"""
    
    suggestions = [
        "What is my deductible for medical services?",
        "How much is a copay for a primary care visit?",
        "What are my out-of-pocket maximums?",
        "Does my plan cover prescription drugs?",
        "Is emergency room care covered?"
    ]
    
    return suggestions

@router.get("/status", response_model=dict)
async def get_query_readiness_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document processing status and query readiness for TPA"""
    
    processing_summary = await document_crud.get_processing_summary(
        db, tpa_id=current_user.tpa_id
    )
    
    return {
        "ready_for_queries": processing_summary['ready_for_queries'],
        "processing_summary": processing_summary,
        "message": "Ready for queries" if processing_summary['ready_for_queries'] 
                  else "Upload and process documents to enable queries"
    }

async def _get_conversation_context(
    db: Session, 
    conversation_id: Optional[str], 
    user_id: str
) -> Optional[dict]:
    """Get conversation context for multi-turn dialogs"""
    
    if not conversation_id:
        return None
    
    try:
        # TODO: Implement conversation storage and retrieval
        # For now, return None to indicate no conversation context
        # In the future, this would query the conversation history
        # and return recent messages for context
        
        # Placeholder conversation context structure:
        # {
        #     "conversation_id": conversation_id,
        #     "previous_queries": ["query1", "query2"],
        #     "previous_responses": ["response1", "response2"],
        #     "context_summary": "User is asking about specialist visits",
        #     "established_context": {
        #         "health_plan_id": "plan123",
        #         "user_role": "member",
        #         "topic_focus": "coverage_inquiry"
        #     }
        # }
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to get conversation context: {e}")
        return None