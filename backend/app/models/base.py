"""
Base model with common fields and functionality
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
import uuid

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UUIDMixin:
    """Mixin for adding UUID primary key"""
    @declared_attr
    def id(cls):
        return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

class TenantMixin:
    """Mixin for multi-tenant support"""
    @declared_attr
    def tpa_id(cls):
        return Column(String(36), nullable=False, index=True)

class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model with UUID primary key and timestamps"""
    __abstract__ = True

class TenantModel(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """Base model for tenant-specific data"""
    __abstract__ = True