"""
Base CRUD operations
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = logging.getLogger(__name__)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    async def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters"""
        query = db.query(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()

    async def count(self, db: Session, **filters) -> int:
        """Count records with filters"""
        query = db.query(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.count()

    async def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        obj_in_data = dict(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record"""
        obj_data = dict(db_obj.__dict__)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def remove(self, db: Session, *, id: int) -> ModelType:
        """Delete a record"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

class TenantCRUDBase(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD for tenant-specific models"""
    
    async def get_by_tpa(
        self, 
        db: Session, 
        *, 
        tpa_id: str, 
        id: Any
    ) -> Optional[ModelType]:
        """Get a single record by ID within a TPA"""
        return db.query(self.model).filter(
            and_(
                self.model.id == id,
                self.model.tpa_id == tpa_id
            )
        ).first()

    async def get_multi_by_tpa(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records within a TPA with pagination and filters"""
        query = db.query(self.model).filter(self.model.tpa_id == tpa_id)
        
        # Apply additional filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()

    async def count_by_tpa(self, db: Session, *, tpa_id: str, **filters) -> int:
        """Count records within a TPA with filters"""
        query = db.query(self.model).filter(self.model.tpa_id == tpa_id)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.count()

    def create_for_tpa(
        self, 
        db: Session, 
        *, 
        obj_in: CreateSchemaType, 
        tpa_id: str
    ) -> ModelType:
        """Create a new record for a specific TPA"""
        if hasattr(obj_in, 'model_dump'):
            obj_in_data = obj_in.model_dump()
        elif hasattr(obj_in, 'dict'):
            obj_in_data = obj_in.dict()
        else:
            obj_in_data = dict(obj_in)
        obj_in_data["tpa_id"] = tpa_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class AuditedCRUDBase(TenantCRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD base class with automatic audit logging"""
    
    def __init__(self, model: Type[ModelType], resource_type: str):
        super().__init__(model)
        self.resource_type = resource_type
    
    async def create_with_audit(
        self,
        db: Session,
        *,
        obj_in: CreateSchemaType,
        tpa_id: str,
        user_id: Optional[str] = None,
        audit_description: Optional[str] = None
    ) -> ModelType:
        """Create a new record with audit logging"""
        try:
            # Create the record
            result = await self.create_for_tpa(db, obj_in=obj_in, tpa_id=tpa_id)
            
            # Log the audit event
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=tpa_id,
                    user_id=user_id,
                    action="create",
                    resource_type=self.resource_type,
                    resource_id=str(result.id),
                    description=audit_description or f"Created {self.resource_type}",
                    severity="medium",
                    new_values=dict(obj_in) if hasattr(obj_in, 'dict') else None,
                    success=True
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for create: {audit_error}")
            
            return result
            
        except Exception as e:
            # Log failed creation attempt
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=tpa_id,
                    user_id=user_id,
                    action="create",
                    resource_type=self.resource_type,
                    description=audit_description or f"Failed to create {self.resource_type}",
                    severity="high",
                    success=False,
                    error_message=str(e)
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for failed create: {audit_error}")
            
            raise
    
    async def update_with_audit(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        user_id: Optional[str] = None,
        audit_description: Optional[str] = None
    ) -> ModelType:
        """Update a record with audit logging"""
        try:
            # Capture old values for audit
            old_values = {
                key: getattr(db_obj, key) 
                for key in dir(db_obj) 
                if not key.startswith('_') and hasattr(db_obj, key)
            }
            
            # Update the record
            result = await self.update(db, db_obj=db_obj, obj_in=obj_in)
            
            # Prepare new values
            new_values = dict(obj_in) if isinstance(obj_in, dict) else (
                obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else None
            )
            
            # Log the audit event
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=getattr(db_obj, 'tpa_id', 'system'),
                    user_id=user_id,
                    action="update",
                    resource_type=self.resource_type,
                    resource_id=str(db_obj.id),
                    description=audit_description or f"Updated {self.resource_type}",
                    severity="medium",
                    old_values=old_values,
                    new_values=new_values,
                    success=True
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for update: {audit_error}")
            
            return result
            
        except Exception as e:
            # Log failed update attempt
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=getattr(db_obj, 'tpa_id', 'system'),
                    user_id=user_id,
                    action="update",
                    resource_type=self.resource_type,
                    resource_id=str(db_obj.id),
                    description=audit_description or f"Failed to update {self.resource_type}",
                    severity="high",
                    success=False,
                    error_message=str(e)
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for failed update: {audit_error}")
            
            raise
    
    async def remove_with_audit(
        self,
        db: Session,
        *,
        id: Any,
        tpa_id: str,
        user_id: Optional[str] = None,
        audit_description: Optional[str] = None
    ) -> ModelType:
        """Delete a record with audit logging"""
        try:
            # Get the object first for audit logging
            db_obj = await self.get_by_tpa(db, tpa_id=tpa_id, id=id)
            if not db_obj:
                raise ValueError(f"{self.resource_type} not found")
            
            # Capture values for audit
            old_values = {
                key: getattr(db_obj, key) 
                for key in dir(db_obj) 
                if not key.startswith('_') and hasattr(db_obj, key)
            }
            
            # Delete the record
            result = await self.remove(db, id=id)
            
            # Log the audit event
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=tpa_id,
                    user_id=user_id,
                    action="delete",
                    resource_type=self.resource_type,
                    resource_id=str(id),
                    description=audit_description or f"Deleted {self.resource_type}",
                    severity="high",
                    old_values=old_values,
                    success=True
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for delete: {audit_error}")
            
            return result
            
        except Exception as e:
            # Log failed deletion attempt
            try:
                from app.services.audit_service import AuditService
                await AuditService.log_event(
                    db=db,
                    tpa_id=tpa_id,
                    user_id=user_id,
                    action="delete",
                    resource_type=self.resource_type,
                    resource_id=str(id),
                    description=audit_description or f"Failed to delete {self.resource_type}",
                    severity="high",
                    success=False,
                    error_message=str(e)
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log audit event for failed delete: {audit_error}")
            
            raise