"""
Analytics service for tracking and analyzing system usage
"""
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.crud.analytics import query_analytics_crud, user_activity_crud
from app.crud.conversation import conversation_crud
from app.crud.document import document_crud
from app.crud.user import user_crud
from app.schemas.analytics import (
    PerformanceStats, QueryTrend, ActivitySummary, 
    DashboardStats, AnalyticsResponse
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics tracking and reporting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def track_query(
        self,
        db: Session,
        query_text: str,
        response_data: Dict[str, Any],
        tpa_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        health_plan_name: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> str:
        """Track a query and its response for analytics"""
        
        try:
            # Generate query hash for deduplication
            query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:64]
            
            # Extract analytics data from response
            query_data = {
                'query_text': query_text[:1000],  # Truncate if too long
                'query_hash': query_hash,
                'query_intent': response_data.get('query_intent', ''),
                'query_complexity': response_data.get('query_complexity', ''),
                'response_time': Decimal(str(response_data.get('processing_time', 0))),
                'confidence_score': Decimal(str(response_data.get('confidence_score', 0))),
                'token_count': response_data.get('token_count', 0),
                'documents_retrieved': len(response_data.get('source_documents', [])),
                'sources_cited': len(response_data.get('source_documents', [])),
                'health_plan_name': health_plan_name or '',
                'user_role': user_role or '',
                'session_info': {
                    'timestamp': datetime.now().isoformat(),
                    'related_topics': response_data.get('related_topics', []),
                    'follow_up_suggestions': response_data.get('follow_up_suggestions', [])
                }
            }
            
            # Create query analytics record
            query_record = query_analytics_crud.create_query_record(
                db=db,
                query_data=query_data,
                tpa_id=tpa_id,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Update user activity
            if user_id:
                await self._update_user_activity(
                    db=db,
                    user_id=user_id,
                    tpa_id=tpa_id,
                    response_time=query_data['response_time'],
                    confidence_score=query_data['confidence_score']
                )
            
            self.logger.info(f"Query tracked successfully: {query_record.id}")
            return query_record.id
            
        except Exception as e:
            self.logger.error(f"Failed to track query: {e}")
            raise
    
    async def track_feedback(
        self,
        db: Session,
        query_id: str,
        user_rating: Optional[int] = None,
        was_helpful: Optional[bool] = None,
        feedback_text: Optional[str] = None
    ) -> bool:
        """Track user feedback for a query"""
        
        try:
            updated_record = query_analytics_crud.update_with_feedback(
                db=db,
                query_id=query_id,
                user_rating=user_rating,
                was_helpful=was_helpful,
                feedback_text=feedback_text
            )
            
            if updated_record:
                self.logger.info(f"Feedback tracked for query: {query_id}")
                return True
            else:
                self.logger.warning(f"Query not found for feedback: {query_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to track feedback: {e}")
            return False
    
    async def _update_user_activity(
        self,
        db: Session,
        user_id: str,
        tpa_id: str,
        response_time: Decimal,
        confidence_score: Decimal
    ):
        """Update user activity metrics"""
        
        try:
            # Increment query count
            user_activity_crud.increment_activity(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                activity_type='queries',
                increment=1
            )
            
            # Update performance metrics (simplified - in production you'd want rolling averages)
            today = datetime.now().date()
            activity_data = {
                'avg_response_time': response_time,
                'avg_confidence_score': confidence_score,
                'success_rate': Decimal('0.85') if confidence_score > Decimal('0.7') else Decimal('0.6')
            }
            
            user_activity_crud.update_daily_activity(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                activity_date=today,
                activity_data=activity_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update user activity: {e}")
    
    async def get_dashboard_stats(
        self,
        db: Session,
        tpa_id: str
    ) -> DashboardStats:
        """Get dashboard statistics for the TPA"""
        
        try:
            # Get active conversations (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            active_conversations = conversation_crud.get_active_conversations_count(
                db=db, tpa_id=tpa_id, since=yesterday
            )
            
            # Get documents processed (total)
            documents_processed = document_crud.get_processed_count(db=db, tpa_id=tpa_id)
            
            # Get user activity summary
            activity_summary = user_activity_crud.get_user_activity_summary(
                db=db, tpa_id=tpa_id, days=30
            )
            
            # Get performance stats
            performance_stats = query_analytics_crud.get_performance_stats(
                db=db, tpa_id=tpa_id, start_date=date.today() - timedelta(days=7)
            )
            
            # Format response time
            avg_response_time = performance_stats.get('avg_response_time', 0)
            response_time_str = f"{avg_response_time:.1f}s" if avg_response_time > 0 else "0.0s"
            
            # Get recent activity (mock data for now - in production, query audit logs)
            recent_activity = [
                {
                    "action": "Query resolved",
                    "description": "Health plan deductible question",
                    "time": "2 minutes ago"
                },
                {
                    "action": "Document processed",
                    "description": "Benefits Summary uploaded",
                    "time": "15 minutes ago"
                },
                {
                    "action": "User logged in",
                    "description": "Customer service agent",
                    "time": "1 hour ago"
                }
            ]
            
            return DashboardStats(
                active_conversations=active_conversations or 0,
                documents_processed=documents_processed or 0,
                active_users=activity_summary.get('active_users', 0),
                avg_response_time=response_time_str,
                total_queries_today=performance_stats.get('total_queries', 0),
                success_rate=performance_stats.get('success_rate', 0),
                user_satisfaction=performance_stats.get('avg_rating', 0),
                recent_activity=recent_activity
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard stats: {e}")
            # Return default stats if there's an error
            return DashboardStats(
                active_conversations=0,
                documents_processed=0,
                active_users=0,
                avg_response_time="0.0s",
                total_queries_today=0,
                success_rate=0.0,
                user_satisfaction=0.0,
                recent_activity=[]
            )
    
    async def get_analytics_report(
        self,
        db: Session,
        tpa_id: str,
        days: int = 30
    ) -> AnalyticsResponse:
        """Get comprehensive analytics report"""
        
        try:
            # Get performance statistics
            performance_stats_data = query_analytics_crud.get_performance_stats(
                db=db,
                tpa_id=tpa_id,
                start_date=date.today() - timedelta(days=days)
            )
            performance_stats = PerformanceStats(**performance_stats_data)
            
            # Get query trends
            query_trends_data = query_analytics_crud.get_query_trends(
                db=db, tpa_id=tpa_id, days=days
            )
            query_trends = [QueryTrend(**trend) for trend in query_trends_data]
            
            # Get activity summary
            activity_summary_data = user_activity_crud.get_user_activity_summary(
                db=db, tpa_id=tpa_id, days=days
            )
            activity_summary = ActivitySummary(**activity_summary_data)
            
            # Get dashboard stats
            dashboard_stats = await self.get_dashboard_stats(db=db, tpa_id=tpa_id)
            
            return AnalyticsResponse(
                performance_stats=performance_stats,
                query_trends=query_trends,
                activity_summary=activity_summary,
                dashboard_stats=dashboard_stats
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics report: {e}")
            raise
    
    async def track_document_access(
        self,
        db: Session,
        user_id: str,
        tpa_id: str,
        document_id: str
    ):
        """Track document access for analytics"""
        
        try:
            user_activity_crud.increment_activity(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                activity_type='documents',
                increment=1
            )
            
            self.logger.info(f"Document access tracked: user={user_id}, doc={document_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track document access: {e}")
    
    async def track_conversation_start(
        self,
        db: Session,
        user_id: str,
        tpa_id: str,
        conversation_id: str
    ):
        """Track conversation start for analytics"""
        
        try:
            user_activity_crud.increment_activity(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                activity_type='conversations',
                increment=1
            )
            
            self.logger.info(f"Conversation start tracked: user={user_id}, conv={conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track conversation start: {e}")


# Create analytics service instance
analytics_service = AnalyticsService()