"""
CRUD operations for analytics
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.crud.base import CRUDBase
from app.models.analytics import QueryAnalytics, UserActivity
from app.schemas.analytics import (
    QueryAnalyticsCreate, QueryAnalyticsUpdate,
    UserActivityCreate, UserActivityUpdate
)


class CRUDQueryAnalytics(CRUDBase[QueryAnalytics, QueryAnalyticsCreate, QueryAnalyticsUpdate]):
    """CRUD operations for query analytics"""
    
    def create_query_record(
        self, 
        db: Session, 
        query_data: Dict[str, Any],
        tpa_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> QueryAnalytics:
        """Create a new query analytics record"""
        
        db_obj = QueryAnalytics(
            query_text=query_data.get('query_text', ''),
            query_hash=query_data.get('query_hash', ''),
            query_intent=query_data.get('query_intent', ''),
            query_complexity=query_data.get('query_complexity', ''),
            response_time=query_data.get('response_time', 0),
            confidence_score=query_data.get('confidence_score', 0),
            token_count=query_data.get('token_count', 0),
            documents_retrieved=query_data.get('documents_retrieved', 0),
            sources_cited=query_data.get('sources_cited', 0),
            health_plan_name=query_data.get('health_plan_name', ''),
            user_role=query_data.get('user_role', ''),
            session_info=query_data.get('session_info', {}),
            tpa_id=tpa_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_with_feedback(
        self,
        db: Session,
        query_id: str,
        user_rating: Optional[int] = None,
        was_helpful: Optional[bool] = None,
        feedback_text: Optional[str] = None
    ) -> Optional[QueryAnalytics]:
        """Update query record with user feedback"""
        
        db_obj = db.query(QueryAnalytics).filter(QueryAnalytics.id == query_id).first()
        if not db_obj:
            return None
            
        if user_rating is not None:
            db_obj.user_rating = user_rating
        if was_helpful is not None:
            db_obj.was_helpful = was_helpful
        if feedback_text is not None:
            db_obj.feedback_text = feedback_text
            
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_performance_stats(
        self,
        db: Session,
        tpa_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get performance statistics for queries"""
        
        query = db.query(QueryAnalytics).filter(QueryAnalytics.tpa_id == tpa_id)
        
        if start_date:
            query = query.filter(QueryAnalytics.created_at >= start_date)
        if end_date:
            query = query.filter(QueryAnalytics.created_at <= end_date)
            
        # Calculate stats
        total_queries = query.count()
        
        if total_queries == 0:
            return {
                'total_queries': 0,
                'avg_response_time': 0,
                'avg_confidence_score': 0,
                'avg_rating': 0,
                'success_rate': 0,
                'positive_feedback_rate': 0
            }
        
        stats = query.with_entities(
            func.avg(QueryAnalytics.response_time).label('avg_response_time'),
            func.avg(QueryAnalytics.confidence_score).label('avg_confidence_score'),
            func.avg(QueryAnalytics.user_rating).label('avg_rating'),
            func.count(QueryAnalytics.was_helpful).filter(QueryAnalytics.was_helpful == True).label('helpful_count'),
            func.count(QueryAnalytics.user_rating).filter(QueryAnalytics.user_rating >= 4).label('positive_rating_count')
        ).first()
        
        success_rate = (stats.helpful_count / total_queries * 100) if stats.helpful_count else 0
        positive_feedback_rate = (stats.positive_rating_count / total_queries * 100) if stats.positive_rating_count else 0
        
        return {
            'total_queries': total_queries,
            'avg_response_time': float(stats.avg_response_time or 0),
            'avg_confidence_score': float(stats.avg_confidence_score or 0),
            'avg_rating': float(stats.avg_rating or 0),
            'success_rate': round(success_rate, 2),
            'positive_feedback_rate': round(positive_feedback_rate, 2)
        }
    
    def get_query_trends(
        self,
        db: Session,
        tpa_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get query trends over time"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        results = db.query(
            func.date(QueryAnalytics.created_at).label('date'),
            func.count(QueryAnalytics.id).label('query_count'),
            func.avg(QueryAnalytics.response_time).label('avg_response_time'),
            func.avg(QueryAnalytics.confidence_score).label('avg_confidence')
        ).filter(
            and_(
                QueryAnalytics.tpa_id == tpa_id,
                QueryAnalytics.created_at >= start_date,
                QueryAnalytics.created_at <= end_date
            )
        ).group_by(
            func.date(QueryAnalytics.created_at)
        ).order_by(
            func.date(QueryAnalytics.created_at)
        ).all()
        
        return [
            {
                'date': str(result.date),
                'query_count': result.query_count,
                'avg_response_time': float(result.avg_response_time or 0),
                'avg_confidence': float(result.avg_confidence or 0)
            }
            for result in results
        ]


class CRUDUserActivity(CRUDBase[UserActivity, UserActivityCreate, UserActivityUpdate]):
    """CRUD operations for user activity"""
    
    def update_daily_activity(
        self,
        db: Session,
        user_id: str,
        tpa_id: str,
        activity_date: date,
        activity_data: Dict[str, Any]
    ) -> UserActivity:
        """Update or create daily activity record"""
        
        # Try to get existing record
        db_obj = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.tpa_id == tpa_id,
                UserActivity.activity_date == activity_date
            )
        ).first()
        
        if db_obj:
            # Update existing record
            for key, value in activity_data.items():
                if hasattr(db_obj, key) and value is not None:
                    setattr(db_obj, key, value)
        else:
            # Create new record
            db_obj = UserActivity(
                user_id=user_id,
                tpa_id=tpa_id,
                activity_date=activity_date,
                **activity_data
            )
            db.add(db_obj)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def increment_activity(
        self,
        db: Session,
        user_id: str,
        tpa_id: str,
        activity_type: str,
        increment: int = 1
    ) -> UserActivity:
        """Increment activity counter for today"""
        
        today = datetime.now().date()
        
        # Get or create today's record
        db_obj = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.tpa_id == tpa_id,
                UserActivity.activity_date == today
            )
        ).first()
        
        if not db_obj:
            db_obj = UserActivity(
                user_id=user_id,
                tpa_id=tpa_id,
                activity_date=today,
                queries_count=0,
                conversations_count=0,
                documents_accessed=0,
                active_time_minutes=0
            )
            db.add(db_obj)
        
        # Increment the appropriate counter
        if activity_type == 'queries':
            db_obj.queries_count += increment
        elif activity_type == 'conversations':
            db_obj.conversations_count += increment
        elif activity_type == 'documents':
            db_obj.documents_accessed += increment
        elif activity_type == 'active_time':
            db_obj.active_time_minutes += increment
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_user_activity_summary(
        self,
        db: Session,
        tpa_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary for the TPA"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get active users count
        active_users = db.query(func.count(func.distinct(UserActivity.user_id))).filter(
            and_(
                UserActivity.tpa_id == tpa_id,
                UserActivity.activity_date >= start_date,
                UserActivity.activity_date <= end_date
            )
        ).scalar()
        
        # Get total activity stats
        stats = db.query(
            func.sum(UserActivity.queries_count).label('total_queries'),
            func.sum(UserActivity.conversations_count).label('total_conversations'),
            func.sum(UserActivity.documents_accessed).label('total_documents'),
            func.sum(UserActivity.active_time_minutes).label('total_active_time'),
            func.avg(UserActivity.avg_response_time).label('avg_response_time'),
            func.avg(UserActivity.success_rate).label('avg_success_rate')
        ).filter(
            and_(
                UserActivity.tpa_id == tpa_id,
                UserActivity.activity_date >= start_date,
                UserActivity.activity_date <= end_date
            )
        ).first()
        
        return {
            'active_users': active_users or 0,
            'total_queries': stats.total_queries or 0,
            'total_conversations': stats.total_conversations or 0,
            'total_documents': stats.total_documents or 0,
            'total_active_hours': round((stats.total_active_time or 0) / 60, 1),
            'avg_response_time': float(stats.avg_response_time or 0),
            'avg_success_rate': float(stats.avg_success_rate or 0)
        }


# Create CRUD instances
query_analytics_crud = CRUDQueryAnalytics(QueryAnalytics)
user_activity_crud = CRUDUserActivity(UserActivity)

# Alias for backward compatibility
analytics_crud = query_analytics_crud