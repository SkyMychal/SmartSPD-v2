"""
Query feedback endpoints for improving RAG responses
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
import logging
from datetime import datetime, timedelta

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.feedback import QueryFeedback, FeedbackType
from app.schemas.feedback import FeedbackCreate, FeedbackOut, FeedbackStats
from app.services.audit_service import AuditService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=FeedbackOut)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback for a query response"""
    
    try:
        # Create feedback record
        feedback = QueryFeedback(
            query_id=feedback_data.query_id,
            feedback_type=feedback_data.feedback_type,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
            suggested_improvement=feedback_data.suggested_improvement,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            # TODO: Store original query and response for analysis
            # original_query=...,
            # original_response=...,
            # response_confidence=...
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        # Audit log the feedback submission
        await AuditService.log_query_event(
            db=db,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            query_text=f"Feedback submitted for query {feedback_data.query_id}",
            success=True,
            metadata={
                "feedback_type": feedback_data.feedback_type.value,
                "rating": feedback_data.rating,
                "has_comment": bool(feedback_data.comment),
                "has_suggestion": bool(feedback_data.suggested_improvement)
            }
        )
        
        logger.info(f"Feedback submitted by user {current_user.id} for query {feedback_data.query_id}")
        
        return feedback
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback statistics for the TPA"""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get feedback within date range for this TPA
    feedback_query = db.query(QueryFeedback).filter(
        QueryFeedback.tpa_id == current_user.tpa_id,
        QueryFeedback.created_at >= start_date,
        QueryFeedback.created_at <= end_date
    )
    
    # Total feedback count
    total_feedback = feedback_query.count()
    
    # Average rating
    avg_rating_result = db.query(func.avg(QueryFeedback.rating)).filter(
        QueryFeedback.tpa_id == current_user.tpa_id,
        QueryFeedback.created_at >= start_date,
        QueryFeedback.created_at <= end_date
    ).scalar()
    
    average_rating = float(avg_rating_result) if avg_rating_result else 0.0
    
    # Feedback breakdown by type
    feedback_breakdown = {}
    for feedback_type in FeedbackType:
        count = feedback_query.filter(
            QueryFeedback.feedback_type == feedback_type
        ).count()
        feedback_breakdown[feedback_type.value] = count
    
    # Recent feedback (last 10)
    recent_feedback_records = feedback_query.order_by(
        desc(QueryFeedback.created_at)
    ).limit(10).all()
    
    recent_feedback = []
    for feedback in recent_feedback_records:
        recent_feedback.append({
            "id": feedback.id,
            "query_id": feedback.query_id,
            "feedback_type": feedback.feedback_type.value,
            "rating": feedback.rating,
            "comment": feedback.comment[:100] + "..." if feedback.comment and len(feedback.comment) > 100 else feedback.comment,
            "created_at": feedback.created_at,
            "user_name": feedback.user.full_name if feedback.user else "Unknown"
        })
    
    return FeedbackStats(
        total_feedback=total_feedback,
        average_rating=average_rating,
        feedback_breakdown=feedback_breakdown,
        recent_feedback=recent_feedback
    )

@router.get("/", response_model=List[FeedbackOut])
async def list_feedback(
    skip: int = 0,
    limit: int = 50,
    feedback_type: str = None,
    min_rating: int = None,
    max_rating: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List feedback for the TPA with filtering options"""
    
    # Base query
    query = db.query(QueryFeedback).filter(
        QueryFeedback.tpa_id == current_user.tpa_id
    )
    
    # Apply filters
    if feedback_type and feedback_type in [ft.value for ft in FeedbackType]:
        query = query.filter(QueryFeedback.feedback_type == feedback_type)
    
    if min_rating is not None:
        query = query.filter(QueryFeedback.rating >= min_rating)
    
    if max_rating is not None:
        query = query.filter(QueryFeedback.rating <= max_rating)
    
    # Order by most recent first
    query = query.order_by(desc(QueryFeedback.created_at))
    
    # Apply pagination
    feedback_list = query.offset(skip).limit(limit).all()
    
    return feedback_list

@router.get("/{feedback_id}", response_model=FeedbackOut)
async def get_feedback(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific feedback details"""
    
    feedback = db.query(QueryFeedback).filter(
        QueryFeedback.id == feedback_id,
        QueryFeedback.tpa_id == current_user.tpa_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return feedback

@router.get("/query/{query_id}", response_model=List[FeedbackOut])
async def get_query_feedback(
    query_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all feedback for a specific query"""
    
    feedback_list = db.query(QueryFeedback).filter(
        QueryFeedback.query_id == query_id,
        QueryFeedback.tpa_id == current_user.tpa_id
    ).order_by(desc(QueryFeedback.created_at)).all()
    
    return feedback_list