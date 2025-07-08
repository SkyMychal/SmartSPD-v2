"""
Analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.audit import audit_endpoint
from app.models.user import User
from app.services.analytics_service import analytics_service
from app.schemas.analytics import (
    AnalyticsResponse, DashboardStats, QueryFeedback, 
    FeedbackResponse, PerformanceStats
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
@audit_endpoint(action="get_dashboard_stats", resource_type="analytics", severity="medium")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for the current user's TPA"""
    
    try:
        stats = await analytics_service.get_dashboard_stats(
            db=db, 
            tpa_id=current_user.tpa_id
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {e}")


@router.get("/report", response_model=AnalyticsResponse)
@audit_endpoint(action="get_analytics_report", resource_type="analytics", severity="high")
async def get_analytics_report(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics report"""
    
    try:
        report = await analytics_service.get_analytics_report(
            db=db,
            tpa_id=current_user.tpa_id,
            days=days
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics report: {e}")


@router.get("/performance", response_model=PerformanceStats)
@audit_endpoint(action="get_performance_stats", resource_type="analytics", severity="medium")
async def get_performance_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days for performance stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance statistics"""
    
    try:
        from app.crud.analytics import query_analytics_crud
        from datetime import date, timedelta
        
        stats_data = query_analytics_crud.get_performance_stats(
            db=db,
            tpa_id=current_user.tpa_id,
            start_date=date.today() - timedelta(days=days)
        )
        return PerformanceStats(**stats_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {e}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_query_feedback(
    feedback: QueryFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback for a query"""
    
    try:
        success = await analytics_service.track_feedback(
            db=db,
            query_id=feedback.query_id,
            user_rating=feedback.user_rating,
            was_helpful=feedback.was_helpful,
            feedback_text=feedback.feedback_text
        )
        
        if success:
            return FeedbackResponse(
                success=True,
                message="Feedback submitted successfully",
                query_id=feedback.query_id
            )
        else:
            return FeedbackResponse(
                success=False,
                message="Query not found or feedback could not be submitted",
                query_id=feedback.query_id
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e}")


@router.get("/usage")
@audit_endpoint(action="get_usage_analytics", resource_type="analytics", severity="medium")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for usage analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage analytics (legacy endpoint)"""
    
    try:
        from app.crud.analytics import user_activity_crud
        
        activity_summary = user_activity_crud.get_user_activity_summary(
            db=db,
            tpa_id=current_user.tpa_id,
            days=days
        )
        
        return {
            "period_days": days,
            "tpa_id": current_user.tpa_id,
            "usage_summary": activity_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage analytics: {e}")