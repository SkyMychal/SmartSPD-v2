"""
Simple document upload endpoint that works
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import uuid
import hashlib
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenData
from app.core.config import settings
from app.models.document import Document, DocumentType, ProcessingStatus

router = APIRouter()

@router.post("/simple-upload")
async def simple_upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(None),
    current_user: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Simple document upload that actually works"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Basic validation
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(file_content) > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Validate document type
        if document_type not in ['BPS', 'SPD']:
            raise HTTPException(status_code=400, detail="Invalid document type")
        
        # Generate file hash and path
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        
        # Create upload directory
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / safe_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create document record directly in database
        document = Document(
            tpa_id=current_user.tpa_id,
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(file_content),
            mime_type=file.content_type or 'application/octet-stream',
            file_hash=file_hash,
            document_type=DocumentType.BPS if document_type == 'BPS' else DocumentType.SPD,
            title=title or file.filename,
            uploaded_by=current_user.user_id,
            processing_status=ProcessingStatus.UPLOADED
        )
        
        # Save to database
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "id": document.id,
            "filename": document.original_filename,
            "title": document.title,
            "document_type": document.document_type.value,
            "file_size": document.file_size,
            "status": "uploaded",
            "message": "Document uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")