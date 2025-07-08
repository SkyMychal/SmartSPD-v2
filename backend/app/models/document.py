"""
Document models for SPD files and BPS data
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, LargeBinary, Enum, Numeric
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import TenantModel

class DocumentType(PyEnum):
    """Document type enumeration"""
    SPD = "spd"           # Summary Plan Description (PDF)
    BPS = "bps"           # Benefit Plan Specification (Excel)
    AMENDMENT = "amendment"
    CERTIFICATE = "certificate"
    OTHER = "other"

class ProcessingStatus(PyEnum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class Document(TenantModel):
    """Document model for uploaded files"""
    __tablename__ = "documents"
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64))  # SHA-256 hash for deduplication
    
    # Document metadata
    document_type = Column(Enum(DocumentType), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    version = Column(String(50), default="1.0")
    
    # Processing status
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED, nullable=False)
    processing_error = Column(Text)
    processing_log = Column(JSON)
    
    # Extracted metadata
    extracted_metadata = Column(JSON)  # Metadata extracted during processing
    page_count = Column(Integer)       # For PDFs
    
    # Access control
    is_public = Column(Boolean, default=False)
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    health_plan_id = Column(String(36), ForeignKey("health_plans.id"))
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tpa = relationship("TPA", back_populates="documents")
    health_plan = relationship("HealthPlan", back_populates="documents")
    uploader = relationship("User")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(filename='{self.filename}', type='{self.document_type.value}')>"

class DocumentChunk(TenantModel):
    """Document chunks for vector search"""
    __tablename__ = "document_chunks"
    
    # Chunk content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64))  # For deduplication
    
    # Chunk metadata
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    section_title = Column(String(255))
    chunk_type = Column(String(50))  # paragraph, table, list, etc.
    
    # Vector embeddings (stored as JSON for compatibility)
    embedding = Column(JSON)  # Vector embedding
    embedding_model = Column(String(100))  # Model used for embedding
    
    # Semantic metadata
    keywords = Column(JSON)  # Extracted keywords
    entities = Column(JSON)  # Named entities
    topics = Column(JSON)    # Topic classification
    
    # Quality scores
    relevance_score = Column(Numeric(5, 4))  # Content relevance score
    confidence_score = Column(Numeric(5, 4))  # Processing confidence
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(document_id='{self.document_id}', chunk_index='{self.chunk_index}')>"