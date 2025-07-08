"""
Query feedback CRUD operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from app.crud.base import TenantCRUDBase
from app.models.feedback import QueryFeedback, FeedbackType
from app.schemas.feedback import FeedbackCreate

class CRUDQueryFeedback(TenantCRUDBase[QueryFeedback, FeedbackCreate, dict]):
    
    def get_by_query_id(
        self,
        db: Session,
        *,
        query_id: str,
        tpa_id: str
    ) -> List[QueryFeedback]:
        """Get all feedback for a specific query"""
        return db.query(QueryFeedback).filter(
            and_(
                QueryFeedback.query_id == query_id,
                QueryFeedback.tpa_id == tpa_id
            )
        ).order_by(desc(QueryFeedback.created_at)).all()
    
    def get_stats(
        self,
        db: Session,
        *,
        tpa_id: str,
        days: int = 30
    ) -> dict:
        """Get feedback statistics for a TPA"""
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        base_query = db.query(QueryFeedback).filter(
            and_(
                QueryFeedback.tpa_id == tpa_id,
                QueryFeedback.created_at >= start_date,
                QueryFeedback.created_at <= end_date
            )
        )
        
        # Total feedback count
        total_feedback = base_query.count()
        
        # Average rating
        avg_rating_result = db.query(func.avg(QueryFeedback.rating)).filter(
            and_(
                QueryFeedback.tpa_id == tpa_id,
                QueryFeedback.created_at >= start_date,
                QueryFeedback.created_at <= end_date
            )
        ).scalar()
        
        average_rating = float(avg_rating_result) if avg_rating_result else 0.0
        
        # Feedback breakdown by type
        feedback_breakdown = {}
        for feedback_type in FeedbackType:
            count = base_query.filter(
                QueryFeedback.feedback_type == feedback_type
            ).count()
            feedback_breakdown[feedback_type.value] = count
        
        return {
            "total_feedback": total_feedback,
            "average_rating": average_rating,
            "feedback_breakdown": feedback_breakdown
        }
    
    def get_recent_feedback(
        self,
        db: Session,
        *,
        tpa_id: str,
        limit: int = 10
    ) -> List[QueryFeedback]:
        """Get recent feedback for a TPA"""
        return db.query(QueryFeedback).filter(
            QueryFeedback.tpa_id == tpa_id
        ).order_by(desc(QueryFeedback.created_at)).limit(limit).all()
    
    def get_feedback_trends(
        self,
        db: Session,
        *,
        tpa_id: str,
        days: int = 30
    ) -> List[dict]:
        """Get feedback trends over time"""
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Group feedback by date
        trends = db.query(
            func.date(QueryFeedback.created_at).label('date'),
            func.count(QueryFeedback.id).label('count'),
            func.avg(QueryFeedback.rating).label('avg_rating')
        ).filter(
            and_(
                QueryFeedback.tpa_id == tpa_id,
                QueryFeedback.created_at >= start_date,
                QueryFeedback.created_at <= end_date
            )
        ).group_by(
            func.date(QueryFeedback.created_at)
        ).order_by(
            func.date(QueryFeedback.created_at)
        ).all()
        
        return [
            {
                "date": trend.date,
                "count": trend.count,
                "average_rating": float(trend.avg_rating) if trend.avg_rating else 0.0
            }
            for trend in trends
        ]

# Create feedback CRUD instance
feedback_crud = CRUDQueryFeedback(QueryFeedback)