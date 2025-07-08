"""
Message CRUD operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from app.crud.base import TenantCRUDBase
from app.models.conversation import Message
from app.schemas.chat import MessageOut

class CRUDMessage(TenantCRUDBase[Message, dict, dict]):
    
    async def get_conversation_messages(
        self,
        db: Session,
        *,
        conversation_id: str,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "asc"  # 'asc' or 'desc'
    ) -> List[Message]:
        """Get messages for a conversation"""
        
        query = db.query(Message).filter(Message.conversation_id == conversation_id)
        
        if order_by == "desc":
            query = query.order_by(desc(Message.created_at))
        else:
            query = query.order_by(Message.created_at)
        
        return query.offset(skip).limit(limit).all()
    
    async def get_recent_messages(
        self,
        db: Session,
        *,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for context"""
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
        
        # Return in chronological order
        return list(reversed(messages))
    
    async def search_messages(
        self,
        db: Session,
        *,
        tpa_id: str,
        search_query: str,
        conversation_id: Optional[str] = None,
        message_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Message]:
        """Search messages by content"""
        
        query = db.query(Message).join(Message.conversation).filter(
            and_(
                Message.conversation.has(tpa_id=tpa_id),
                Message.content.ilike(f"%{search_query}%")
            )
        )
        
        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)
        
        if message_type:
            query = query.filter(Message.message_type == message_type)
        
        return query.order_by(desc(Message.created_at)).offset(skip).limit(limit).all()
    
    async def get_message_stats(
        self,
        db: Session,
        *,
        tpa_id: str,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get message statistics"""
        
        query = db.query(Message).join(Message.conversation).filter(
            Message.conversation.has(tpa_id=tpa_id)
        )
        
        if agent_id:
            query = query.filter(Message.conversation.has(agent_id=agent_id))
        
        if start_date:
            query = query.filter(Message.created_at >= start_date)
        
        if end_date:
            query = query.filter(Message.created_at <= end_date)
        
        # Count by message type
        type_counts = db.query(
            Message.message_type,
            func.count(Message.id)
        ).join(Message.conversation).filter(
            Message.conversation.has(tpa_id=tpa_id)
        ).group_by(Message.message_type).all()
        
        # Messages per day
        daily_counts = db.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).join(Message.conversation).filter(
            Message.conversation.has(tpa_id=tpa_id)
        ).group_by(func.date(Message.created_at)).order_by('date').all()
        
        return {
            "total_messages": query.count(),
            "type_breakdown": {msg_type: count for msg_type, count in type_counts},
            "daily_counts": [
                {"date": str(date), "count": count} 
                for date, count in daily_counts
            ],
            "period_start": start_date,
            "period_end": end_date
        }
    
    async def get_agent_response_time(
        self,
        db: Session,
        *,
        agent_id: str,
        tpa_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate agent response time metrics"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get conversations where agent responded
        conversations = db.query(Message.conversation_id).join(Message.conversation).filter(
            and_(
                Message.conversation.has(tpa_id=tpa_id),
                Message.conversation.has(agent_id=agent_id),
                Message.message_type == "assistant",
                Message.created_at >= start_date
            )
        ).distinct().all()
        
        response_times = []
        
        for (conv_id,) in conversations:
            # Get user messages and their following assistant responses
            messages = db.query(Message).filter(
                and_(
                    Message.conversation_id == conv_id,
                    Message.created_at >= start_date
                )
            ).order_by(Message.created_at).all()
            
            for i, message in enumerate(messages):
                if (message.message_type == "user" and 
                    i + 1 < len(messages) and 
                    messages[i + 1].message_type == "assistant"):
                    
                    response_time = (messages[i + 1].created_at - message.created_at).total_seconds()
                    response_times.append(response_time)
        
        if not response_times:
            return {
                "average_response_time": 0,
                "median_response_time": 0,
                "total_responses": 0
            }
        
        response_times.sort()
        n = len(response_times)
        
        return {
            "average_response_time": sum(response_times) / n,
            "median_response_time": response_times[n // 2],
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "total_responses": n
        }
    
    async def create_system_message(
        self,
        db: Session,
        *,
        conversation_id: str,
        content: str,
        tpa_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Create a system message"""
        
        message_data = {
            "conversation_id": conversation_id,
            "content": content,
            "message_type": "system",
            "metadata": metadata
        }
        
        return await self.create(db=db, obj_in=message_data, tpa_id=tpa_id)
    
    async def flag_message(
        self,
        db: Session,
        *,
        message_id: str,
        flag_reason: str,
        flagged_by: str,
        tpa_id: str
    ) -> Optional[Message]:
        """Flag a message for review"""
        
        message = await self.get(db=db, id=message_id, tpa_id=tpa_id)
        if not message:
            return None
        
        updated_metadata = message.metadata or {}
        updated_metadata.update({
            "flagged": True,
            "flag_reason": flag_reason,
            "flagged_by": flagged_by,
            "flagged_at": datetime.utcnow().isoformat()
        })
        
        return await self.update(
            db=db,
            db_obj=message,
            obj_in={"metadata": updated_metadata}
        )

message_crud = CRUDMessage(Message)