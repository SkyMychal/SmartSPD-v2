"""
CRUD operations for data access
"""
from .user import CRUDUser
from .tpa import CRUDTPA
from .health_plan import CRUDHealthPlan
from .document import CRUDDocument
from .conversation import CRUDConversation
from .message import CRUDMessage
from .analytics import CRUDQueryAnalytics

from app.models.user import User
from app.models.tpa import TPA
from app.models.health_plan import HealthPlan
from app.models.document import Document
from app.models.conversation import Conversation, Message
from app.models.analytics import QueryAnalytics

# Create singleton instances
user_crud = CRUDUser(User)
tpa_crud = CRUDTPA(TPA)
health_plan_crud = CRUDHealthPlan(HealthPlan)
document_crud = CRUDDocument(Document)
conversation_crud = CRUDConversation(Conversation)
message_crud = CRUDMessage(Message)
analytics_crud = CRUDQueryAnalytics(QueryAnalytics)

__all__ = [
    "user_crud",
    "tpa_crud", 
    "health_plan_crud",
    "document_crud",
    "conversation_crud",
    "message_crud",
    "analytics_crud"
]