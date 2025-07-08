"""
User Activity Tracking Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_manager, require_admin
from app.models.user import User
from app.services.user_activity_service import UserActivityService
from app.services.audit_service import AuditService

router = APIRouter()

@router.get("/summary/{user_id}")
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get comprehensive activity summary for a specific user"""
    
    # Check permissions - users can only see their own data unless they're managers
    if current_user.role not in ["tpa_admin", "cs_manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Non-admin users can only see users in their TPA
    if current_user.role != "tpa_admin":
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or target_user.tpa_id != current_user.tpa_id:
            raise HTTPException(status_code=404, detail="User not found")
    
    try:
        summary = await UserActivityService.get_user_activity_summary(
            db=db,
            user_id=user_id,
            days=days
        )
        
        # Log data access
        await AuditService.log_data_access(
            db=db,
            user_id=current_user.id,
            tpa_id=current_user.tpa_id,
            resource_type="user_activity",
            resource_id=user_id,
            action="read",
            description=f"Viewed activity summary for user {user_id}",
            metadata={"analysis_days": days}
        )
        
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/tpa-overview")
async def get_tpa_activity_overview(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get activity overview for a TPA"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        # Non-admin users can only see their own TPA
        target_tpa_id = current_user.tpa_id
    elif not tpa_id:
        # Admin users must specify a TPA ID
        raise HTTPException(status_code=400, detail="TPA ID required for admin users")
    
    overview = await UserActivityService.get_tpa_activity_overview(
        db=db,
        tpa_id=target_tpa_id,
        days=days
    )
    
    # Log admin access
    await AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="tpa_activity",
        resource_id=target_tpa_id,
        action="read",
        description=f"Viewed TPA activity overview for {target_tpa_id}",
        metadata={"analysis_days": days}
    )
    
    return overview

@router.get("/anomaly-detection/{user_id}")
async def detect_user_anomalies(
    user_id: str,
    threshold: float = Query(3.0, ge=1.0, le=10.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Detect unusual activity patterns for a user"""
    
    # Check permissions
    if current_user.role not in ["tpa_admin", "cs_manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Non-admin users can only analyze users in their TPA
    if current_user.role != "tpa_admin":
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or target_user.tpa_id != current_user.tpa_id:
            raise HTTPException(status_code=404, detail="User not found")
    
    anomalies = await UserActivityService.detect_unusual_activity(
        db=db,
        user_id=user_id,
        threshold_multiplier=threshold
    )
    
    # Log security analysis
    await AuditService.log_security_event(
        db=db,
        tpa_id=current_user.tpa_id,
        action="anomaly_detection",
        description=f"Ran anomaly detection for user {user_id}",
        user_id=current_user.id,
        severity="medium" if anomalies["has_unusual_activity"] else "low",
        metadata={
            "target_user_id": user_id,
            "threshold": threshold,
            "anomalies_found": len(anomalies.get("anomalies", []))
        }
    )
    
    return anomalies

@router.get("/engagement-metrics")
async def get_engagement_metrics(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get user engagement metrics"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    
    metrics = await UserActivityService.get_user_engagement_metrics(
        db=db,
        tpa_id=target_tpa_id,
        days=days
    )
    
    return metrics

@router.get("/feature-usage")
async def get_feature_usage_metrics(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get feature usage analytics"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    
    usage_data = await UserActivityService.track_feature_usage(
        db=db,
        tpa_id=target_tpa_id,
        days=days
    )
    
    return usage_data

@router.get("/insights")
async def get_activity_insights(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get actionable insights from user activity data"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    
    insights = await UserActivityService.generate_activity_insights(
        db=db,
        tpa_id=target_tpa_id,
        days=days
    )
    
    # Log insights generation
    await AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="activity_insights",
        resource_id=target_tpa_id or "system",
        action="read",
        description="Generated activity insights report",
        metadata={"analysis_days": days}
    )
    
    return insights

@router.get("/daily-patterns/{user_id}")
async def get_user_daily_patterns(
    user_id: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get detailed daily activity patterns for a user"""
    
    # Check permissions
    if current_user.role not in ["tpa_admin", "cs_manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user's activity summary which includes daily patterns
    summary = await UserActivityService.get_user_activity_summary(
        db=db,
        user_id=user_id,
        days=days
    )
    
    # Extract and enhance daily patterns
    daily_activity = summary.get("daily_activity", {})
    hourly_activity = summary.get("hourly_activity", {})
    
    # Calculate patterns
    patterns = {
        "daily_activity": daily_activity,
        "hourly_activity": hourly_activity,
        "most_active_hour": summary.get("most_active_hour"),
        "avg_daily_activity": sum(daily_activity.values()) / len(daily_activity) if daily_activity else 0,
        "peak_activity_day": max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else None,
        "low_activity_days": [day for day, count in daily_activity.items() if count < (sum(daily_activity.values()) / len(daily_activity) / 2)] if daily_activity else [],
        "activity_consistency": {
            "std_deviation": None,  # Could calculate standard deviation
            "active_days": len([count for count in daily_activity.values() if count > 0]),
            "total_days": len(daily_activity)
        }
    }
    
    return {
        "user_id": user_id,
        "analysis_period": days,
        "patterns": patterns,
        "summary_stats": {
            "total_activities": summary.get("total_activities", 0),
            "avg_activities_per_day": patterns["avg_daily_activity"],
            "most_active_hour": patterns["most_active_hour"]
        }
    }

@router.post("/track-session")
async def track_user_session(
    session_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track a user session (for internal system use)"""
    
    # Only allow users to track their own sessions
    if session_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Can only track your own session")
    
    session_info = await UserActivityService.track_user_session(
        db=db,
        user_id=current_user.id,
        session_start=datetime.fromisoformat(session_data["session_start"]),
        session_end=datetime.fromisoformat(session_data["session_end"]) if session_data.get("session_end") else None,
        ip_address=session_data.get("ip_address"),
        user_agent=session_data.get("user_agent"),
        activities_count=session_data.get("activities_count", 0)
    )
    
    return {"message": "Session tracked successfully", "session_data": session_info}

@router.get("/inactive-users")
async def get_inactive_users(
    tpa_id: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get list of inactive users for re-engagement"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    
    engagement_metrics = await UserActivityService.get_user_engagement_metrics(
        db=db,
        tpa_id=target_tpa_id,
        days=days
    )
    
    inactive_users = engagement_metrics["engagement_distribution"]["inactive"]
    lightly_engaged = engagement_metrics["engagement_distribution"]["lightly_engaged"]
    
    # Combine and sort by last login
    at_risk_users = inactive_users + [u for u in lightly_engaged if u["activity_count"] < 5]
    
    # Sort by last login (most recent first for prioritization)
    at_risk_users.sort(key=lambda x: x["last_login"] or datetime.min, reverse=True)
    
    return {
        "tpa_id": target_tpa_id,
        "analysis_period": days,
        "inactive_users_count": len(inactive_users),
        "lightly_engaged_count": len(lightly_engaged),
        "at_risk_users": at_risk_users[:50],  # Limit to top 50
        "recommendations": [
            "Send re-engagement emails to users with recent but low activity",
            "Provide training sessions for users with no recent activity",
            "Consider removing users inactive for more than 90 days"
        ]
    }

@router.get("/churn-risk/{user_id}")
async def predict_user_churn_risk(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Predict churn risk for a specific user"""
    
    # Check permissions
    if current_user.role not in ["tpa_admin", "cs_manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Non-admin users can only analyze users in their TPA
    if current_user.role != "tpa_admin":
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or target_user.tpa_id != current_user.tpa_id:
            raise HTTPException(status_code=404, detail="User not found")
    
    churn_prediction = await UserActivityService.predict_user_churn_risk(
        db=db,
        user_id=user_id
    )
    
    # Log predictive analytics access
    await AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="churn_prediction",
        resource_id=user_id,
        action="read",
        description=f"Generated churn risk prediction for user {user_id}",
        metadata={"risk_level": churn_prediction.get("risk_level")}
    )
    
    return churn_prediction

@router.get("/user-journey/{user_id}")
async def get_user_journey_analytics(
    user_id: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get detailed user journey analytics"""
    
    # Check permissions
    if current_user.role not in ["tpa_admin", "cs_manager"] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Non-admin users can only analyze users in their TPA
    if current_user.role != "tpa_admin":
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user or target_user.tpa_id != current_user.tpa_id:
            raise HTTPException(status_code=404, detail="User not found")
    
    journey_analytics = await UserActivityService.get_user_journey_analytics(
        db=db,
        user_id=user_id,
        days=days
    )
    
    # Log journey analytics access
    await AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="user_journey",
        resource_id=user_id,
        action="read",
        description=f"Analyzed user journey for user {user_id}",
        metadata={"analysis_days": days}
    )
    
    return journey_analytics

@router.get("/real-time-activity")
async def get_real_time_activity(
    tpa_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get real-time activity monitoring data"""
    
    # Determine which TPA to monitor
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    
    real_time_data = await UserActivityService.track_real_time_activity(
        db=db,
        tpa_id=target_tpa_id,
        hours=hours
    )
    
    # Log monitoring access
    await AuditService.log_data_access(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        resource_type="real_time_monitoring",
        resource_id=target_tpa_id or "system",
        action="read",
        description=f"Accessed real-time activity monitoring",
        metadata={"monitoring_hours": hours}
    )
    
    return real_time_data

@router.get("/batch-churn-analysis")
async def run_batch_churn_analysis(
    tpa_id: Optional[str] = Query(None),
    risk_threshold: str = Query("medium", regex="^(low|medium|high)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Run batch churn risk analysis for all users in a TPA"""
    
    # Determine which TPA to analyze
    target_tpa_id = tpa_id
    if current_user.role != "tpa_admin":
        target_tpa_id = current_user.tpa_id
    elif not tpa_id:
        raise HTTPException(status_code=400, detail="TPA ID required for admin users")
    
    # Get all users in the TPA
    users_query = db.query(User).filter(User.tpa_id == target_tpa_id, User.is_active == True)
    users = users_query.all()
    
    # Analyze churn risk for each user
    churn_analysis = {
        "high_risk": [],
        "medium_risk": [],
        "low_risk": [],
        "very_low_risk": [],
        "unknown": []
    }
    
    total_analyzed = 0
    for user in users:
        try:
            prediction = await UserActivityService.predict_user_churn_risk(
                db=db,
                user_id=user.id
            )
            
            risk_level = prediction.get("risk_level", "unknown")
            user_info = {
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}",
                "user_email": user.email,
                "risk_score": prediction.get("risk_score", 0),
                "risk_factors": prediction.get("risk_factors", []),
                "recommendations": prediction.get("recommendations", [])
            }
            
            if risk_level in churn_analysis:
                churn_analysis[risk_level].append(user_info)
            else:
                churn_analysis["unknown"].append(user_info)
            
            total_analyzed += 1
            
        except Exception as e:
            logger.warning(f"Failed to analyze churn risk for user {user.id}: {e}")
    
    # Filter results based on threshold
    threshold_levels = {
        "high": ["high_risk"],
        "medium": ["high_risk", "medium_risk"],
        "low": ["high_risk", "medium_risk", "low_risk"]
    }
    
    filtered_results = {}
    for level in threshold_levels[risk_threshold]:
        filtered_results[level] = churn_analysis[level]
    
    # Log batch analysis
    await AuditService.log_admin_action(
        db=db,
        user_id=current_user.id,
        tpa_id=current_user.tpa_id,
        action="batch_churn_analysis",
        description=f"Performed batch churn analysis for TPA {target_tpa_id}",
        resource_type="analytics",
        metadata={
            "target_tpa_id": target_tpa_id,
            "users_analyzed": total_analyzed,
            "risk_threshold": risk_threshold
        }
    )
    
    return {
        "tpa_id": target_tpa_id,
        "total_users_analyzed": total_analyzed,
        "risk_threshold": risk_threshold,
        "analysis_results": filtered_results,
        "summary": {
            "high_risk_count": len(churn_analysis["high_risk"]),
            "medium_risk_count": len(churn_analysis["medium_risk"]),
            "low_risk_count": len(churn_analysis["low_risk"]),
            "total_at_risk": len(churn_analysis["high_risk"]) + len(churn_analysis["medium_risk"])
        }
    }