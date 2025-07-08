"""
Document management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import uuid
import hashlib
import logging
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user_token, require_agent, TokenData
from app.core.config import settings
from app.core.exceptions import ValidationError, DocumentProcessingError
from app.schemas.document import DocumentOut, DocumentList, DocumentUpload, DocumentCreate
from app.models.document import Document, DocumentType, ProcessingStatus
from app.crud.document import document_crud
from app.services.document_processor import DocumentProcessor
from app.services.batch_document_processor import batch_document_processor
from app.services.document_version_control import document_version_control
from app.services.audit_service import AuditService
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    health_plan_id: Optional[str] = None,
    processing_status: Optional[str] = None,
    current_user: TokenData = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """List documents for current TPA"""
    
    # Build filters
    filters = {}
    if document_type:
        try:
            filters['document_type'] = DocumentType(document_type)
        except ValueError:
            raise ValidationError(f"Invalid document type: {document_type}")
    
    if health_plan_id:
        filters['health_plan_id'] = health_plan_id
    
    if processing_status:
        try:
            filters['processing_status'] = ProcessingStatus(processing_status)
        except ValueError:
            raise ValidationError(f"Invalid processing status: {processing_status}")
    
    # Build query for documents
    query = db.query(Document).filter(Document.tpa_id == current_user.tpa_id)
    
    # Apply filters
    if filters.get('document_type'):
        query = query.filter(Document.document_type == filters['document_type'])
    if filters.get('health_plan_id'):
        query = query.filter(Document.health_plan_id == filters['health_plan_id'])
    if filters.get('processing_status'):
        query = query.filter(Document.processing_status == filters['processing_status'])
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    documents = query.offset(skip).limit(limit).all()
    
    return DocumentList(
        documents=[DocumentOut.from_orm(doc) for doc in documents],
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        size=limit
    )

@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    health_plan_id: Optional[str] = Form(None),
    document_type: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: TokenData = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """Upload and process document (SPD PDF or BPS Excel)"""
    
    # Validate file type
    allowed_types = {
        'pdf': ['application/pdf'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'xls': ['application/vnd.ms-excel'],
        'csv': ['text/csv']
    }
    
    file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
    
    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise ValidationError(f"Invalid document type: {document_type}")
    
    try:
        # Read file content first
        file_content = await file.read()
        
        # Check file size after reading content
        if len(file_content) > settings.MAX_FILE_SIZE_BYTES:
            raise ValidationError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB")
        
        # Validate file extension matches document type
        if doc_type == DocumentType.SPD and file_extension != 'pdf':
            raise ValidationError("SPD documents must be PDF files")
        elif doc_type == DocumentType.BPS and file_extension not in ['xlsx', 'xls', 'csv']:
            raise ValidationError("BPS documents must be Excel or CSV files")
        
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for duplicate files
        existing_doc = document_crud.get_by_hash(db, file_hash=file_hash, tpa_id=current_user.tpa_id)
        if existing_doc:
            raise ValidationError("This file has already been uploaded")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        
        # Save file to upload directory
        upload_dir = Path(settings.UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / unique_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create document record
        document = Document(
            tpa_id=current_user.tpa_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(file_content),
            mime_type=file.content_type,
            file_hash=file_hash,
            document_type=doc_type,
            title=title or file.filename,
            description=description,
            uploaded_by=current_user.user_id,
            health_plan_id=health_plan_id,
            processing_status=ProcessingStatus.UPLOADED
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Log upload event
        AuditService.log_event(
            db=db,
            tpa_id=current_user.tpa_id,
            user_id=current_user.user_id,
            action="upload",
            resource_type="document",
            resource_id=document.id,
            description=f"Document uploaded: {file.filename}",
            metadata={
                "document_type": document_type,
                "file_size": len(file_content),
                "file_hash": file_hash
            }
        )
        
        # Schedule background processing
        background_tasks.add_task(process_document_background, document.id, str(file_path))
        
        return DocumentOut.from_orm(document)
        
    except Exception as e:
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        if isinstance(e, ValidationError):
            raise e
        else:
            raise DocumentProcessingError(f"Failed to upload document: {str(e)}")

@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    current_user: TokenData = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """Get document by ID"""
    
    document = document_crud.get(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check TPA access
    if document.tpa_id != current_user.tpa_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DocumentOut.from_orm(document)

@router.post("/{document_id}/process")
def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """Manually trigger document processing for knowledge graph"""
    
    # Use direct query instead of CRUD to avoid async issues
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tpa_id == current_user.tpa_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status to processing
    document.processing_status = ProcessingStatus.PROCESSING
    db.commit()
    
    # Schedule background processing
    background_tasks.add_task(process_document_background, document_id, document.file_path)
    
    # Return appropriate message based on document type
    process_type = "RAG chunking" if document.document_type == DocumentType.SPD else "knowledge graph extraction"
    
    return {
        "message": f"Document processing started for {process_type}",
        "document_id": document_id,
        "document_type": document.document_type.value,
        "process_type": process_type,
        "status": "processing"
    }

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: TokenData = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """Delete a document and its associated data"""
    
    # Use direct query to avoid CRUD async issues
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tpa_id == current_user.tpa_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete associated document chunks
        from app.models.document import DocumentChunk
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Delete the file from storage
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
            logger.info(f"Deleted file: {document.file_path}")
        
        # Delete the document record
        db.delete(document)
        db.commit()
        
        # Log deletion event
        AuditService.log_event(
            db=db,
            tpa_id=current_user.tpa_id,
            user_id=current_user.user_id,
            action="delete",
            resource_type="document",
            resource_id=document_id,
            description=f"Document deleted: {document.original_filename}",
            metadata={"document_type": document.document_type.value}
        )
        
        logger.info(f"Document {document_id} ({document.original_filename}) deleted successfully")
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

async def process_document_background(document_id: str, file_path: str):
    """Background task to process uploaded document with notifications and tracking"""
    from app.core.database import SessionLocal
    from app.services.notification_service import NotificationService
    from app.crud.user import user_crud
    import time
    
    db_session = SessionLocal()
    start_time = time.time()
    
    try:
        # Use direct query to avoid CRUD async issues
        document = db_session.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for background processing")
            return
        
        logger.info(f"Starting background processing for document {document_id}: {document.original_filename}")
        
        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        db_session.commit()
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Process the document with detailed logging
        logger.info(f"Processing {document.document_type.value} document: {document.original_filename}")
        success = await processor.process_document(db_session, document, file_path)
        
        processing_time = time.time() - start_time
        
        if success:
            document.processing_status = ProcessingStatus.COMPLETED
            logger.info(f"Document {document_id} processed successfully in {processing_time:.1f}s")
            
            # Send completion notification to admin
            try:
                # Get TPA admin user for notifications
                admin_user = db_session.query(User).filter(
                    User.tpa_id == document.tpa_id,
                    User.role == "tpa_admin"
                ).first()
                
                if admin_user:
                    notification_service = NotificationService()
                    await notification_service.notify_document_processed(
                        db=db_session,
                        document_id=document_id,
                        document_name=document.original_filename,
                        user_email=admin_user.email,
                        processing_status="completed",
                        processing_time=processing_time
                    )
                    logger.info(f"Completion notification sent to admin: {admin_user.email}")
                else:
                    logger.warning(f"No admin user found for TPA {document.tpa_id}")
                    
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")
        else:
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = "Processing failed"
            logger.error(f"Document {document_id} processing failed after {processing_time:.1f}s")
        
        db_session.commit()
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Document processing exception after {processing_time:.1f}s: {e}")
        
        # Update document status to failed
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = ProcessingStatus.FAILED
                document.processing_error = str(e)
                db_session.commit()
                
                # Send failure notification
                try:
                    admin_user = db_session.query(User).filter(
                        User.tpa_id == document.tpa_id,
                        User.role == "tpa_admin"
                    ).first()
                    
                    if admin_user:
                        notification_service = NotificationService()
                        await notification_service.notify_document_processed(
                            db=db_session,
                            document_id=document_id,
                            document_name=document.original_filename,
                            user_email=admin_user.email,
                            processing_status="failed",
                            processing_time=processing_time
                        )
                except Exception as notify_error:
                    logger.error(f"Failed to send failure notification: {notify_error}")
        except Exception as update_error:
            logger.error(f"Failed to update document status: {update_error}")
    finally:
        db_session.close()