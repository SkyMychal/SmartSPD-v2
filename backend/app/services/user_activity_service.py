"""
User Activity Tracking Service

This service provides comprehensive user activity monitoring and analytics,
connecting to existing audit logs and user activity models.
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from app.models.user import User
from app.models.audit import AuditLog
from app.crud.analytics import analytics_crud
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class UserActivityService:
    """Service for tracking and analyzing user activity patterns"""
    
    @staticmethod
    async def track_user_session(
        db: Session,
        user_id: str,
        session_start: datetime,
        session_end: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        activities_count: int = 0
    ) -> Dict[str, Any]:
        """Track a user session with activities"""
        
        session_duration = None
        if session_end:
            session_duration = (session_end - session_start).total_seconds()
        
        session_data = {
            "user_id": user_id,
            "session_start": session_start,
            "session_end": session_end,
            "session_duration_seconds": session_duration,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "activities_count": activities_count
        }
        
        # Log session start as audit event
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            await AuditService.log_auth_event(
                db=db,
                user_id=user_id,
                tpa_id=user.tpa_id,
                action="session_start",
                description=f"User session started",
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
        
        return session_data
    
    @staticmethod
    async def get_user_activity_summary(
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive activity summary for a user"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get audit logs for the user
        user_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= start_date
            )
        ).all()
        
        # Calculate activity metrics
        total_activities = len(user_logs)
        successful_activities = len([log for log in user_logs if log.success])
        failed_activities = total_activities - successful_activities
        
        # Group by action type
        action_breakdown = {}
        for log in user_logs:
            action_breakdown[log.action] = action_breakdown.get(log.action, 0) + 1
        
        # Group by resource type
        resource_breakdown = {}
        for log in user_logs:
            resource_breakdown[log.resource_type] = resource_breakdown.get(log.resource_type, 0) + 1
        
        # Calculate daily activity
        daily_activity = {}
        for log in user_logs:
            day = log.created_at.date().isoformat()
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        # Get login sessions
        login_logs = [log for log in user_logs if log.action in ["login", "session_start"]]
        unique_ips = list(set([log.ip_address for log in user_logs if log.ip_address]))
        
        # Most active hours
        hourly_activity = {}
        for log in user_logs:
            hour = log.created_at.hour
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
        
        return {
            "user_id": user_id,
            "user_email": user.email,
            "user_name": f"{user.first_name} {user.last_name}",
            "user_role": user.role,
            "tpa_id": user.tpa_id,
            "period_days": days,
            "total_activities": total_activities,
            "successful_activities": successful_activities,
            "failed_activities": failed_activities,
            "success_rate": (successful_activities / total_activities * 100) if total_activities > 0 else 0,
            "login_sessions": len(login_logs),
            "unique_ip_addresses": len(unique_ips),
            "action_breakdown": action_breakdown,
            "resource_breakdown": resource_breakdown,
            "daily_activity": daily_activity,
            "hourly_activity": hourly_activity,
            "most_active_hour": most_active_hour,
            "last_activity": max([log.created_at for log in user_logs]) if user_logs else None,
            "first_activity": min([log.created_at for log in user_logs]) if user_logs else None
        }
    
    @staticmethod
    async def get_tpa_activity_overview(
        db: Session,
        tpa_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity overview for an entire TPA"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all users in the TPA
        tpa_users = db.query(User).filter(User.tpa_id == tpa_id).all()
        user_ids = [user.id for user in tpa_users]
        
        # Get audit logs for all TPA users
        tpa_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.tpa_id == tpa_id,
                AuditLog.created_at >= start_date
            )
        ).all()
        
        # Active users (users with activity in the period)
        active_user_ids = list(set([log.user_id for log in tpa_logs if log.user_id]))
        active_users_count = len(active_user_ids)
        
        # Calculate metrics
        total_activities = len(tpa_logs)
        successful_activities = len([log for log in tpa_logs if log.success])
        
        # Top users by activity
        user_activity_counts = {}
        for log in tpa_logs:
            if log.user_id:
                user_activity_counts[log.user_id] = user_activity_counts.get(log.user_id, 0) + 1
        
        top_users = sorted(user_activity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_users_data = []
        for user_id, count in top_users:
            user = next((u for u in tpa_users if u.id == user_id), None)
            if user:
                top_users_data.append({
                    "user_id": user_id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "user_email": user.email,
                    "activity_count": count
                })
        
        # Daily activity trend
        daily_activity = {}
        for log in tpa_logs:
            day = log.created_at.date().isoformat()
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        # Action breakdown
        action_breakdown = {}
        for log in tpa_logs:
            action_breakdown[log.action] = action_breakdown.get(log.action, 0) + 1
        
        return {
            "tpa_id": tpa_id,
            "period_days": days,
            "total_users": len(tpa_users),
            "active_users": active_users_count,
            "user_engagement_rate": (active_users_count / len(tpa_users) * 100) if tpa_users else 0,
            "total_activities": total_activities,
            "successful_activities": successful_activities,
            "success_rate": (successful_activities / total_activities * 100) if total_activities > 0 else 0,
            "avg_activities_per_user": total_activities / len(tpa_users) if tpa_users else 0,
            "top_users": top_users_data,
            "daily_activity": daily_activity,
            "action_breakdown": action_breakdown
        }
    
    @staticmethod
    async def detect_unusual_activity(
        db: Session,
        user_id: str,
        threshold_multiplier: float = 3.0
    ) -> Dict[str, Any]:
        """Detect unusual activity patterns for a user"""
        
        # Get user's historical activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        user_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= thirty_days_ago
            )
        ).all()
        
        if len(user_logs) < 10:  # Not enough data
            return {"has_unusual_activity": False, "reason": "insufficient_data"}
        
        # Calculate daily activity counts
        daily_counts = {}
        for log in user_logs:
            day = log.created_at.date()
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        counts = list(daily_counts.values())
        avg_daily_activity = sum(counts) / len(counts)
        
        # Check today's activity
        today = datetime.utcnow().date()
        today_activity = daily_counts.get(today, 0)
        
        # Detect anomalies
        anomalies = []
        
        # High activity anomaly
        if today_activity > avg_daily_activity * threshold_multiplier:
            anomalies.append({
                "type": "high_activity",
                "description": f"Activity {today_activity} is {today_activity/avg_daily_activity:.1f}x higher than average",
                "severity": "medium" if today_activity < avg_daily_activity * 5 else "high"
            })
        
        # Check for unusual IP addresses
        recent_ips = [log.ip_address for log in user_logs[-20:] if log.ip_address]  # Last 20 activities
        historical_ips = [log.ip_address for log in user_logs[:-20] if log.ip_address]
        
        new_ips = set(recent_ips) - set(historical_ips)
        if new_ips:
            anomalies.append({
                "type": "new_ip_address",
                "description": f"Activity from {len(new_ips)} new IP address(es): {', '.join(list(new_ips)[:3])}",
                "severity": "medium"
            })
        
        # Check for failed login patterns
        recent_failed_logins = [
            log for log in user_logs[-50:] 
            if log.action in ["login", "authentication"] and not log.success
        ]
        
        if len(recent_failed_logins) > 5:
            anomalies.append({
                "type": "multiple_failed_logins",
                "description": f"{len(recent_failed_logins)} failed login attempts detected",
                "severity": "high"
            })
        
        # Check for off-hours activity
        business_hours = range(8, 18)  # 8 AM to 6 PM
        off_hours_activity = [
            log for log in user_logs[-20:] 
            if log.created_at.hour not in business_hours
        ]
        
        if len(off_hours_activity) > len(user_logs[-20:]) * 0.5:  # More than 50% off-hours
            anomalies.append({
                "type": "off_hours_activity",
                "description": f"High off-hours activity: {len(off_hours_activity)} out of last 20 activities",
                "severity": "low"
            })
        
        return {
            "has_unusual_activity": len(anomalies) > 0,
            "anomalies": anomalies,
            "avg_daily_activity": avg_daily_activity,
            "today_activity": today_activity,
            "analysis_period_days": 30
        }
    
    @staticmethod
    async def get_user_engagement_metrics(
        db: Session,
        tpa_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user engagement metrics across the platform"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        query = db.query(User)
        if tpa_id:
            query = query.filter(User.tpa_id == tpa_id)
        
        all_users = query.all()
        
        # Get audit logs for the period
        logs_query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)
        if tpa_id:
            logs_query = logs_query.filter(AuditLog.tpa_id == tpa_id)
        
        all_logs = logs_query.all()
        
        # Calculate engagement levels
        user_activity_counts = {}
        for log in all_logs:
            if log.user_id:
                user_activity_counts[log.user_id] = user_activity_counts.get(log.user_id, 0) + 1
        
        # Categorize users by engagement
        highly_engaged = []  # >100 activities
        moderately_engaged = []  # 20-100 activities
        lightly_engaged = []  # 1-19 activities
        inactive = []  # 0 activities
        
        for user in all_users:
            activity_count = user_activity_counts.get(user.id, 0)
            user_data = {
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}",
                "user_email": user.email,
                "activity_count": activity_count,
                "last_login": user.last_login_at
            }
            
            if activity_count > 100:
                highly_engaged.append(user_data)
            elif activity_count >= 20:
                moderately_engaged.append(user_data)
            elif activity_count > 0:
                lightly_engaged.append(user_data)
            else:
                inactive.append(user_data)
        
        # Calculate retention metrics
        total_users = len(all_users)
        active_users = len([u for u in all_users if u.id in user_activity_counts])
        
        return {
            "period_days": days,
            "total_users": total_users,
            "active_users": active_users,
            "engagement_rate": (active_users / total_users * 100) if total_users > 0 else 0,
            "highly_engaged_users": len(highly_engaged),
            "moderately_engaged_users": len(moderately_engaged),
            "lightly_engaged_users": len(lightly_engaged),
            "inactive_users": len(inactive),
            "engagement_distribution": {
                "highly_engaged": highly_engaged[:10],  # Top 10
                "moderately_engaged": moderately_engaged[:10],
                "lightly_engaged": lightly_engaged[:10],
                "inactive": inactive[:10]
            },
            "avg_activities_per_active_user": sum(user_activity_counts.values()) / len(user_activity_counts) if user_activity_counts else 0
        }
    
    @staticmethod
    async def track_feature_usage(
        db: Session,
        tpa_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Track usage of different platform features"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get audit logs for the period
        logs_query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)
        if tpa_id:
            logs_query = logs_query.filter(AuditLog.tpa_id == tpa_id)
        
        all_logs = logs_query.all()
        
        # Feature mapping based on actions and resource types
        feature_mapping = {
            "chat_queries": ["query", "conversation"],
            "document_management": ["upload", "download", "document"],
            "user_management": ["user_create", "user_update", "user_delete"],
            "analytics_viewing": ["analytics", "dashboard"],
            "admin_functions": ["admin_action", "tpa_management"],
            "authentication": ["login", "logout", "session_start"]
        }
        
        feature_usage = {}
        feature_users = {}
        
        for feature, actions in feature_mapping.items():
            feature_logs = [
                log for log in all_logs 
                if log.action in actions or log.resource_type in actions
            ]
            
            feature_usage[feature] = len(feature_logs)
            feature_users[feature] = len(set([log.user_id for log in feature_logs if log.user_id]))
        
        # Calculate daily usage trends
        daily_feature_usage = {}
        for log in all_logs:
            day = log.created_at.date().isoformat()
            if day not in daily_feature_usage:
                daily_feature_usage[day] = {}
            
            for feature, actions in feature_mapping.items():
                if log.action in actions or log.resource_type in actions:
                    daily_feature_usage[day][feature] = daily_feature_usage[day].get(feature, 0) + 1
        
        return {
            "period_days": days,
            "feature_usage_counts": feature_usage,
            "feature_unique_users": feature_users,
            "daily_feature_usage": daily_feature_usage,
            "most_used_feature": max(feature_usage.items(), key=lambda x: x[1])[0] if feature_usage else None,
            "least_used_feature": min(feature_usage.items(), key=lambda x: x[1])[0] if feature_usage else None
        }
    
    @staticmethod
    async def generate_activity_insights(
        db: Session,
        tpa_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate actionable insights from user activity data"""
        
        # Get various metrics
        engagement_metrics = await UserActivityService.get_user_engagement_metrics(db, tpa_id, days)
        feature_usage = await UserActivityService.track_feature_usage(db, tpa_id, days)
        
        if tpa_id:
            tpa_overview = await UserActivityService.get_tpa_activity_overview(db, tpa_id, days)
        else:
            tpa_overview = None
        
        insights = []
        recommendations = []
        
        # Engagement insights
        engagement_rate = engagement_metrics["engagement_rate"]
        if engagement_rate < 50:
            insights.append("Low user engagement detected")
            recommendations.append("Consider user training sessions or feature walkthroughs")
        elif engagement_rate > 80:
            insights.append("High user engagement - platform is well adopted")
        
        # Feature usage insights
        feature_counts = feature_usage["feature_usage_counts"]
        if feature_counts.get("chat_queries", 0) < feature_counts.get("document_management", 0):
            insights.append("Users are uploading documents but not actively querying")
            recommendations.append("Promote query features and provide sample questions")
        
        # Inactive user insights
        inactive_count = engagement_metrics["inactive_users"]
        total_users = engagement_metrics["total_users"]
        if inactive_count > total_users * 0.3:
            insights.append(f"High number of inactive users ({inactive_count} out of {total_users})")
            recommendations.append("Implement user re-engagement campaigns")
        
        # Activity pattern insights
        if tpa_overview:
            avg_activities = tpa_overview["avg_activities_per_user"]
            if avg_activities < 10:
                insights.append("Low average activity per user")
                recommendations.append("Investigate barriers to platform usage")
        
        return {
            "analysis_period": days,
            "tpa_id": tpa_id,
            "insights": insights,
            "recommendations": recommendations,
            "engagement_summary": {
                "engagement_rate": engagement_rate,
                "total_users": engagement_metrics["total_users"],
                "active_users": engagement_metrics["active_users"]
            },
            "top_features": sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    @staticmethod
    async def predict_user_churn_risk(
        db: Session,
        user_id: str,
        prediction_days: int = 7
    ) -> Dict[str, Any]:
        """Predict likelihood of user churn based on activity patterns"""
        
        # Get user's historical activity for longer period
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        user_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= ninety_days_ago
            )
        ).order_by(AuditLog.created_at.desc()).all()
        
        if len(user_logs) < 5:
            return {"risk_level": "unknown", "reason": "insufficient_data"}
        
        # Calculate activity trend
        recent_activity = len([
            log for log in user_logs 
            if log.created_at >= datetime.utcnow() - timedelta(days=7)
        ])
        
        previous_week_activity = len([
            log for log in user_logs 
            if log.created_at >= datetime.utcnow() - timedelta(days=14) and
            log.created_at < datetime.utcnow() - timedelta(days=7)
        ])
        
        month_ago_activity = len([
            log for log in user_logs 
            if log.created_at >= datetime.utcnow() - timedelta(days=30) and
            log.created_at < datetime.utcnow() - timedelta(days=23)
        ])
        
        # Risk factors
        risk_factors = []
        risk_score = 0
        
        # Declining activity trend
        if recent_activity < previous_week_activity * 0.5:
            risk_factors.append("Activity declining sharply")
            risk_score += 30
        
        # No activity in recent days
        if recent_activity == 0:
            risk_factors.append("No activity in past 7 days")
            risk_score += 40
        
        # Low overall activity
        avg_weekly_activity = (recent_activity + previous_week_activity + month_ago_activity) / 3
        if avg_weekly_activity < 3:
            risk_factors.append("Consistently low activity")
            risk_score += 20
        
        # Failed activities trend
        recent_failed = len([
            log for log in user_logs[:20] if not log.success
        ])
        if recent_failed > 5:
            risk_factors.append("High failure rate in recent activities")
            risk_score += 25
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        elif risk_score >= 20:
            risk_level = "low"
        else:
            risk_level = "very_low"
        
        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recent_activity": recent_activity,
            "previous_week_activity": previous_week_activity,
            "activity_trend": "declining" if recent_activity < previous_week_activity else "stable" if recent_activity == previous_week_activity else "increasing",
            "recommendations": UserActivityService._get_churn_prevention_recommendations(risk_level)
        }
    
    @staticmethod
    def _get_churn_prevention_recommendations(risk_level: str) -> List[str]:
        """Get recommendations based on churn risk level"""
        recommendations = {
            "high": [
                "Send immediate re-engagement email",
                "Offer personalized training session",
                "Check for technical issues or access problems",
                "Consider account manager outreach"
            ],
            "medium": [
                "Send feature highlight email",
                "Provide usage tips and best practices",
                "Monitor closely for next 2 weeks"
            ],
            "low": [
                "Include in general engagement campaigns",
                "Monitor activity patterns"
            ],
            "very_low": [
                "User appears to be actively engaged"
            ]
        }
        return recommendations.get(risk_level, [])
    
    @staticmethod
    async def get_user_journey_analytics(
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze user journey and feature adoption patterns"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        user_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= start_date
            )
        ).order_by(AuditLog.created_at.asc()).all()
        
        if not user_logs:
            return {"user_id": user_id, "journey_data": None}
        
        # Feature adoption timeline
        feature_first_use = {}
        feature_usage_count = {}
        
        for log in user_logs:
            feature = log.resource_type
            if feature not in feature_first_use:
                feature_first_use[feature] = log.created_at
            feature_usage_count[feature] = feature_usage_count.get(feature, 0) + 1
        
        # User progression stages
        stages = {
            "onboarding": ["authentication", "login"],
            "exploration": ["dashboard", "analytics"],
            "content_creation": ["document", "upload"],
            "active_usage": ["query", "conversation"],
            "advanced_usage": ["admin", "user_management"]
        }
        
        stage_completion = {}
        for stage, actions in stages.items():
            completed = any(action in [log.action for log in user_logs] or 
                          action in [log.resource_type for log in user_logs] 
                          for action in actions)
            stage_completion[stage] = completed
        
        # Activity frequency patterns
        weekly_activity = {}
        for log in user_logs:
            week = log.created_at.isocalendar()[1]
            weekly_activity[week] = weekly_activity.get(week, 0) + 1
        
        return {
            "user_id": user_id,
            "analysis_period": days,
            "feature_adoption": {
                "first_use_dates": {k: v.isoformat() for k, v in feature_first_use.items()},
                "usage_counts": feature_usage_count,
                "total_features_used": len(feature_first_use)
            },
            "user_progression": {
                "stages_completed": stage_completion,
                "progression_score": sum(stage_completion.values()) / len(stage_completion) * 100
            },
            "activity_patterns": {
                "weekly_activity": weekly_activity,
                "most_active_week": max(weekly_activity.items(), key=lambda x: x[1])[0] if weekly_activity else None,
                "consistency_score": len(weekly_activity) / (days // 7) * 100 if days >= 7 else 100
            },
            "journey_insights": UserActivityService._generate_journey_insights(stage_completion, feature_usage_count)
        }
    
    @staticmethod
    def _generate_journey_insights(stage_completion: Dict[str, bool], feature_usage: Dict[str, int]) -> List[str]:
        """Generate insights about user journey"""
        insights = []
        
        if not stage_completion.get("onboarding"):
            insights.append("User has not completed basic onboarding")
        elif not stage_completion.get("exploration"):
            insights.append("User needs guidance on platform exploration")
        elif not stage_completion.get("active_usage"):
            insights.append("User is not actively using core features")
        elif stage_completion.get("advanced_usage"):
            insights.append("User is a power user with advanced feature usage")
        else:
            insights.append("User is progressing well through the platform")
        
        # Feature usage insights
        if feature_usage.get("document", 0) > 0 and feature_usage.get("conversation", 0) == 0:
            insights.append("User uploads documents but doesn't query them")
        
        if feature_usage.get("authentication", 0) > feature_usage.get("query", 0) * 2:
            insights.append("User logs in frequently but has low activity")
        
        return insights
    
    @staticmethod
    async def track_real_time_activity(
        db: Session,
        tpa_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Track real-time activity metrics for monitoring dashboard"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get recent audit logs
        logs_query = db.query(AuditLog).filter(AuditLog.created_at >= start_time)
        if tpa_id:
            logs_query = logs_query.filter(AuditLog.tpa_id == tpa_id)
        
        recent_logs = logs_query.all()
        
        # Calculate real-time metrics
        total_activities = len(recent_logs)
        unique_users = len(set([log.user_id for log in recent_logs if log.user_id]))
        failed_activities = len([log for log in recent_logs if not log.success])
        
        # Hourly breakdown
        hourly_activity = {}
        for log in recent_logs:
            hour = log.created_at.hour
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        # Current hour activity
        current_hour = datetime.utcnow().hour
        current_hour_activity = hourly_activity.get(current_hour, 0)
        
        # Action breakdown for current period
        action_breakdown = {}
        for log in recent_logs:
            action_breakdown[log.action] = action_breakdown.get(log.action, 0) + 1
        
        # Security events in timeframe
        security_events = [log for log in recent_logs if log.resource_type == "security"]
        
        return {
            "timeframe_hours": hours,
            "total_activities": total_activities,
            "unique_active_users": unique_users,
            "failed_activities": failed_activities,
            "failure_rate": (failed_activities / total_activities * 100) if total_activities > 0 else 0,
            "activities_per_hour": total_activities / hours,
            "current_hour_activity": current_hour_activity,
            "hourly_breakdown": hourly_activity,
            "top_actions": sorted(action_breakdown.items(), key=lambda x: x[1], reverse=True)[:5],
            "security_events_count": len(security_events),
            "real_time_alerts": UserActivityService._generate_real_time_alerts(
                total_activities, failed_activities, len(security_events), hours
            )
        }
    
    @staticmethod
    def _generate_real_time_alerts(
        total_activities: int, 
        failed_activities: int, 
        security_events: int, 
        hours: int
    ) -> List[Dict[str, Any]]:
        """Generate real-time alerts based on activity patterns"""
        alerts = []
        
        failure_rate = (failed_activities / total_activities * 100) if total_activities > 0 else 0
        
        if failure_rate > 20:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "high",
                "message": f"High failure rate detected: {failure_rate:.1f}%",
                "recommendation": "Check system health and user access issues"
            })
        
        if security_events > 5:
            alerts.append({
                "type": "security_events",
                "severity": "medium",
                "message": f"{security_events} security events in last {hours} hours",
                "recommendation": "Review security logs for potential threats"
            })
        
        activities_per_hour = total_activities / hours
        if activities_per_hour < 1 and hours <= 8:  # During business hours
            alerts.append({
                "type": "low_activity",
                "severity": "low",
                "message": f"Low activity detected: {activities_per_hour:.1f} activities/hour",
                "recommendation": "Monitor for system issues or user access problems"
            })
        
        return alerts