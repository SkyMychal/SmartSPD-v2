"""
User model with role-based access control
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime, JSON, Integer
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import TenantModel

class UserRole(PyEnum):
    """User role enumeration"""
    TPA_ADMIN = "tpa_admin"           # Full TPA access
    CS_MANAGER = "cs_manager"         # Customer service manager
    CS_AGENT = "cs_agent"             # Customer service agent
    MEMBER = "member"                 # Health plan member (read-only)
    READONLY = "readonly"             # Read-only access

class User(TenantModel):
    """User model with multi-tenant support"""
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Role and permissions
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CS_AGENT)
    permissions = Column(JSON, default=list)  # Additional granular permissions
    
    # Profile
    phone = Column(String(50))
    department = Column(String(100))
    title = Column(String(100))
    
    # Session management
    last_login_at = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Multi-factor authentication
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))  # Encrypted
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    
    # Relationships
    tpa = relationship("TPA", back_populates="users")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("QueryFeedback", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role == UserRole.TPA_ADMIN
    
    @property
    def can_manage_users(self):
        return self.role in [UserRole.TPA_ADMIN, UserRole.CS_MANAGER]
    
    @property
    def can_upload_documents(self):
        return self.role in [UserRole.TPA_ADMIN, UserRole.CS_MANAGER]
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role.value}')>"