"""
Document schemas
"""
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    SPD = "spd"
    BPS = "bps"
    AMENDMENT = "amendment"
    CERTIFICATE = "certificate"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class DocumentBase(BaseModel):
    """Base document schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: DocumentType
    health_plan_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    """Document creation schema"""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_hash: Optional[str] = None
    uploaded_by: str
    version: str = "1.0"

class DocumentUpdate(BaseModel):
    """Document update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    processing_status: Optional[ProcessingStatus] = None
    processing_error: Optional[str] = None
    processing_log: Optional[Dict[str, Any]] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    page_count: Optional[int] = None

class DocumentUpload(BaseModel):
    """Document upload request schema"""
    health_plan_id: Optional[str] = None
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None

class DocumentOut(DocumentBase):
    """Document output schema"""
    id: str
    tpa_id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_hash: Optional[str] = None
    version: str
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    page_count: Optional[int] = None
    is_public: bool
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    """Document list response"""
    documents: List[DocumentOut]
    total: int
    page: int
    size: int

class DocumentChunkOut(BaseModel):
    """Document chunk output schema"""
    id: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    relevance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentProcessingStats(BaseModel):
    """Document processing statistics"""
    total_documents: int
    uploaded: int
    processing: int
    completed: int
    failed: int
    archived: int
    success_rate: float