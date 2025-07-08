"""
Conversation CRUD operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from app.crud.base import TenantCRUDBase
from app.models.conversation import Conversation, Message
from app.schemas.chat import ConversationCreate, ConversationUpdate

class CRUDConversation(TenantCRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    
    async def get_conversations(
        self,
        db: Session,
        *,
        tpa_id: str,
        agent_id: Optional[str] = None,
        member_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """Get conversations with filters"""
        
        query = db.query(Conversation).filter(Conversation.tpa_id == tpa_id)
        
        if agent_id:
            query = query.filter(Conversation.agent_id == agent_id)
        
        if member_id:
            query = query.filter(Conversation.member_id == member_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        # Order by most recent activity
        query = query.order_by(desc(Conversation.updated_at))
        
        conversations = query.offset(skip).limit(limit).all()
        
        # Add message count and last message time for each conversation
        for conversation in conversations:
            message_stats = db.query(
                func.count(Message.id).label('count'),
                func.max(Message.created_at).label('last_message')
            ).filter(
                Message.conversation_id == conversation.id
            ).first()
            
            conversation.message_count = message_stats.count if message_stats.count else 0
            conversation.last_message_at = message_stats.last_message
        
        return conversations
    
    async def count_conversations(
        self,
        db: Session,
        *,
        tpa_id: str,
        agent_id: Optional[str] = None,
        member_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count conversations with filters"""
        
        query = db.query(func.count(Conversation.id)).filter(Conversation.tpa_id == tpa_id)
        
        if agent_id:
            query = query.filter(Conversation.agent_id == agent_id)
        
        if member_id:
            query = query.filter(Conversation.member_id == member_id)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.scalar() or 0
    
    async def get_active_conversations(
        self,
        db: Session,
        *,
        tpa_id: str,
        agent_id: Optional[str] = None
    ) -> List[Conversation]:
        """Get active conversations"""
        
        query = db.query(Conversation).filter(
            and_(
                Conversation.tpa_id == tpa_id,
                Conversation.status == "active"
            )
        )
        
        if agent_id:
            query = query.filter(Conversation.agent_id == agent_id)
        
        return query.order_by(desc(Conversation.updated_at)).all()
    
    async def get_conversation_with_messages(
        self,
        db: Session,
        *,
        conversation_id: str,
        tpa_id: str,
        limit: int = 50
    ) -> Optional[Conversation]:
        """Get conversation with recent messages"""
        
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.tpa_id == tpa_id
            )
        ).first()
        
        if not conversation:
            return None
        
        # Get recent messages
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
        
        # Reverse to get chronological order
        conversation.messages = list(reversed(messages))
        
        return conversation
    
    async def search_conversations(
        self,
        db: Session,
        *,
        tpa_id: str,
        search_query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by title or content"""
        
        # Search in conversation titles and message content
        conversations = db.query(Conversation).join(Message, isouter=True).filter(
            and_(
                Conversation.tpa_id == tpa_id,
                or_(
                    Conversation.title.ilike(f"%{search_query}%"),
                    Message.content.ilike(f"%{search_query}%")
                )
            )
        ).distinct().order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
        
        return conversations
    
    async def get_conversation_stats(
        self,
        db: Session,
        *,
        tpa_id: str,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get conversation statistics"""
        
        query = db.query(Conversation).filter(Conversation.tpa_id == tpa_id)
        
        if agent_id:
            query = query.filter(Conversation.agent_id == agent_id)
        
        if start_date:
            query = query.filter(Conversation.created_at >= start_date)
        
        if end_date:
            query = query.filter(Conversation.created_at <= end_date)
        
        # Count by status
        status_counts = db.query(
            Conversation.status,
            func.count(Conversation.id)
        ).filter(Conversation.tpa_id == tpa_id).group_by(Conversation.status).all()
        
        # Average messages per conversation
        avg_messages = db.query(
            func.avg(
                db.query(func.count(Message.id)).filter(
                    Message.conversation_id == Conversation.id
                ).scalar_subquery()
            )
        ).filter(Conversation.tpa_id == tpa_id).scalar()
        
        return {
            "total_conversations": query.count(),
            "status_breakdown": {status: count for status, count in status_counts},
            "average_messages_per_conversation": float(avg_messages or 0),
            "period_start": start_date,
            "period_end": end_date
        }
    
    async def assign_conversation(
        self,
        db: Session,
        *,
        conversation_id: str,
        agent_id: str,
        tpa_id: str
    ) -> Optional[Conversation]:
        """Assign conversation to an agent"""
        
        conversation = await self.get(db=db, id=conversation_id, tpa_id=tpa_id)
        if not conversation:
            return None
        
        return await self.update(
            db=db,
            db_obj=conversation,
            obj_in={"agent_id": agent_id, "updated_at": datetime.utcnow()}
        )
    
    async def escalate_conversation(
        self,
        db: Session,
        *,
        conversation_id: str,
        tpa_id: str,
        escalation_reason: str
    ) -> Optional[Conversation]:
        """Escalate conversation to supervisor"""
        
        conversation = await self.get(db=db, id=conversation_id, tpa_id=tpa_id)
        if not conversation:
            return None
        
        return await self.update(
            db=db,
            db_obj=conversation,
            obj_in={
                "status": "escalated",
                "priority": "high",
                "updated_at": datetime.utcnow(),
                "metadata": {
                    **(conversation.metadata or {}),
                    "escalation_reason": escalation_reason,
                    "escalated_at": datetime.utcnow().isoformat()
                }
            }
        )
    
    def get_active_conversations_count(
        self,
        db: Session,
        *,
        tpa_id: str,
        since: Optional[datetime] = None
    ) -> int:
        """Get count of active conversations, optionally since a specific time"""
        
        query = db.query(func.count(Conversation.id)).filter(
            and_(
                Conversation.tpa_id == tpa_id,
                Conversation.status == "active"
            )
        )
        
        if since:
            query = query.filter(Conversation.updated_at >= since)
        
        return query.scalar() or 0
    
    async def get_by_tpa(self, db: Session, *, tpa_id: str) -> List[Conversation]:
        """Get all conversations for a TPA"""
        return db.query(Conversation).filter(Conversation.tpa_id == tpa_id).all()

conversation_crud = CRUDConversation(Conversation)