"""
Document CRUD operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, text, func

from app.crud.base import TenantCRUDBase
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentCreate, DocumentUpdate

class CRUDDocument(TenantCRUDBase[Document, DocumentCreate, DocumentUpdate]):
    
    def get_by_hash(
        self, 
        db: Session, 
        *, 
        file_hash: str, 
        tpa_id: str
    ) -> Optional[Document]:
        """Get document by file hash within TPA"""
        return db.query(Document).filter(
            and_(
                Document.file_hash == file_hash,
                Document.tpa_id == tpa_id
            )
        ).first()
    
    async def get_by_health_plan(
        self, 
        db: Session, 
        *, 
        health_plan_id: str,
        tpa_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents for specific health plan"""
        return db.query(Document).filter(
            and_(
                Document.health_plan_id == health_plan_id,
                Document.tpa_id == tpa_id
            )
        ).offset(skip).limit(limit).all()
    
    async def search_chunks(
        self,
        db: Session,
        *,
        tpa_id: str,
        query: str,
        health_plan_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 15
    ) -> List[DocumentChunk]:
        """Search document chunks with enhanced filtering - ONLY COMPLETED DOCUMENTS"""
        from app.models.document import ProcessingStatus
        
        # Base query with TPA filtering AND processing status check
        base_query = db.query(DocumentChunk).join(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == ProcessingStatus.COMPLETED
            )
        )
        
        # Add health plan filter if specified
        if health_plan_id:
            base_query = base_query.filter(Document.health_plan_id == health_plan_id)
        
        # Add document type filter if specified
        if document_type:
            base_query = base_query.filter(Document.document_type == document_type)
        
        # Full-text search on content
        if query:
            # Use PostgreSQL full-text search if available
            search_terms = query.lower().split()
            for term in search_terms:
                base_query = base_query.filter(
                    func.lower(DocumentChunk.content).contains(term)
                )
        
        # Order by relevance score and confidence
        results = base_query.order_by(
            DocumentChunk.relevance_score.desc(),
            DocumentChunk.confidence_score.desc()
        ).limit(limit).all()
        
        return results
    
    async def has_processed_documents(
        self, 
        db: Session, 
        *, 
        tpa_id: str,
        health_plan_id: Optional[str] = None
    ) -> bool:
        """Check if TPA has any fully processed documents available for queries"""
        from app.models.document import ProcessingStatus
        
        query = db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == ProcessingStatus.COMPLETED
            )
        )
        
        if health_plan_id:
            query = query.filter(Document.health_plan_id == health_plan_id)
        
        return query.first() is not None
    
    async def get_processing_summary(
        self, 
        db: Session, 
        *, 
        tpa_id: str
    ) -> dict:
        """Get comprehensive processing status summary for TPA"""
        from app.models.document import ProcessingStatus
        
        total = db.query(Document).filter(Document.tpa_id == tpa_id).count()
        completed = db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == ProcessingStatus.COMPLETED
            )
        ).count()
        processing = db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == ProcessingStatus.PROCESSING
            )
        ).count()
        failed = db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == ProcessingStatus.FAILED
            )
        ).count()
        
        return {
            'total_documents': total,
            'completed': completed,
            'processing': processing,
            'failed': failed,
            'uploaded': total - completed - processing - failed,
            'ready_for_queries': completed > 0
        }
    
    async def get_processing_status_count(
        self, 
        db: Session, 
        *, 
        tpa_id: str
    ) -> dict:
        """Get count of documents by processing status"""
        from sqlalchemy import func
        from app.models.document import ProcessingStatus
        
        result = db.query(
            Document.processing_status,
            func.count(Document.id).label('count')
        ).filter(
            Document.tpa_id == tpa_id
        ).group_by(Document.processing_status).all()
        
        status_counts = {status.value: 0 for status in ProcessingStatus}
        for status, count in result:
            status_counts[status.value] = count
        
        return status_counts
    
    def get_processed_count(
        self, 
        db: Session, 
        *, 
        tpa_id: str
    ) -> int:
        """Get count of successfully processed documents"""
        from sqlalchemy import func
        
        return db.query(func.count(Document.id)).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.processing_status == "completed"
            )
        ).scalar() or 0
    
    async def get_by_batch(
        self,
        db: Session,
        *,
        batch_id: str,
        tpa_id: str
    ) -> List[Document]:
        """Get documents by batch ID"""
        return db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.metadata['batch_id'].astext == batch_id
            )
        ).all()
    
    async def get_failed_by_batch(
        self,
        db: Session,
        *,
        batch_id: str,
        tpa_id: str
    ) -> List[Document]:
        """Get failed documents by batch ID"""
        return db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.metadata['batch_id'].astext == batch_id,
                Document.processing_status == "failed"
            )
        ).all()

class CRUDDocumentChunk(TenantCRUDBase[DocumentChunk, dict, dict]):
    
    async def get_by_document(
        self,
        db: Session,
        *,
        document_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """Get chunks for specific document"""
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).offset(skip).limit(limit).all()
    
    async def search_chunks(
        self,
        db: Session,
        *,
        tpa_id: str,
        query: str,
        health_plan_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 20
    ) -> List[DocumentChunk]:
        """Search chunks by content"""
        from sqlalchemy import text
        
        # Build the query
        base_query = db.query(DocumentChunk).filter(
            DocumentChunk.tpa_id == tpa_id
        )
        
        # Add health plan filter
        if health_plan_id:
            base_query = base_query.join(Document).filter(
                Document.health_plan_id == health_plan_id
            )
        
        # Add document type filter
        if document_type:
            base_query = base_query.join(Document).filter(
                Document.document_type == document_type
            )
        
        # Add text search
        base_query = base_query.filter(
            DocumentChunk.content.ilike(f"%{query}%")
        )
        
        # Order by relevance score and limit
        return base_query.order_by(
            DocumentChunk.relevance_score.desc(),
            DocumentChunk.confidence_score.desc()
        ).limit(limit).all()

# Add missing method to CRUDDocument
CRUDDocument.get_processed_count = lambda self, db, *, tpa_id: db.query(Document).filter(
    and_(Document.tpa_id == tpa_id, Document.processing_status == "completed")
).count()

CRUDDocument.get_by_tpa = lambda self, db, *, tpa_id: db.query(Document).filter(Document.tpa_id == tpa_id).all()

# Create instances
document_crud = CRUDDocument(Document)
document_chunk_crud = CRUDDocumentChunk(DocumentChunk)