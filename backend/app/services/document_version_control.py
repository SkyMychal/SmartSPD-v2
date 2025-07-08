"""
Document version control service for tracking document changes and versions
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import difflib
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.exceptions import DocumentProcessingError
from app.models.document import Document, DocumentType
from app.crud.document import document_crud
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)


class DocumentVersion:
    """Represents a document version"""
    
    def __init__(self, document: Document):
        self.document_id = document.id
        self.version_number = self._get_version_from_metadata(document)
        self.file_hash = document.file_hash
        self.filename = document.filename
        self.file_size = document.file_size
        self.created_at = document.created_at
        self.metadata = document.metadata or {}
        self.processing_status = document.processing_status
    
    def _get_version_from_metadata(self, document: Document) -> int:
        """Extract version number from document metadata"""
        metadata = document.metadata or {}
        return metadata.get('version_number', 1)


class DocumentVersionControl:
    """Service for managing document versions and changes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def upload_new_version(
        self,
        db: Session,
        file_path: str,
        original_document_id: str,
        tpa_id: str,
        user_id: str,
        change_notes: Optional[str] = None
    ) -> Tuple[Document, Dict[str, Any]]:
        """Upload a new version of an existing document"""
        
        try:
            # Get original document
            original_doc = await document_crud.get(db, id=original_document_id, tpa_id=tpa_id)
            if not original_doc:
                raise DocumentProcessingError("Original document not found")
            
            # Calculate new file hash
            new_file_hash = self._calculate_file_hash(file_path)
            
            # Check if file content has actually changed
            if new_file_hash == original_doc.file_hash:
                return original_doc, {
                    'version_created': False,
                    'reason': 'File content unchanged',
                    'current_version': self._get_current_version_number(db, original_document_id, tpa_id)
                }
            
            # Get current version number
            current_version = self._get_current_version_number(db, original_document_id, tpa_id)
            new_version = current_version + 1
            
            # Create new version document
            import os
            from pathlib import Path
            
            path = Path(file_path)
            
            new_doc_data = {
                'filename': original_doc.filename,  # Keep original filename
                'file_path': file_path,
                'file_size': path.stat().st_size,
                'file_hash': new_file_hash,
                'document_type': original_doc.document_type,
                'health_plan_id': original_doc.health_plan_id,
                'processing_status': 'pending',
                'metadata': {
                    **original_doc.metadata,
                    'version_number': new_version,
                    'original_document_id': original_document_id,
                    'previous_version': current_version,
                    'change_notes': change_notes or f"Version {new_version} uploaded",
                    'uploaded_by': user_id,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'is_version': True
                }
            }
            
            # Create new document version
            new_document = await document_crud.create(db, obj_in=new_doc_data, tpa_id=tpa_id)
            
            # Archive previous version
            await self._archive_previous_version(db, original_doc, new_version)
            
            # Generate change summary
            change_summary = await self._generate_change_summary(
                db, original_doc, new_document, tpa_id
            )
            
            # Track version creation analytics
            await analytics_service.track_document_access(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                document_id=new_document.id
            )
            
            self.logger.info(f"Created version {new_version} for document {original_document_id}")
            
            return new_document, {
                'version_created': True,
                'new_version_number': new_version,
                'previous_version': current_version,
                'change_summary': change_summary,
                'new_document_id': new_document.id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload new version: {e}")
            raise DocumentProcessingError(f"Failed to upload new version: {e}")
    
    def _get_current_version_number(self, db: Session, original_document_id: str, tpa_id: str) -> int:
        """Get the current highest version number for a document"""
        
        # Find all versions of this document
        versions = db.query(Document).filter(
            and_(
                Document.tpa_id == tpa_id,
                Document.metadata['original_document_id'].astext == original_document_id
            )
        ).all()
        
        # Include the original document
        original = db.query(Document).filter(
            and_(
                Document.id == original_document_id,
                Document.tpa_id == tpa_id
            )
        ).first()
        
        if original:
            versions.append(original)
        
        # Find highest version number
        max_version = 1
        for doc in versions:
            metadata = doc.metadata or {}
            version_num = metadata.get('version_number', 1)
            max_version = max(max_version, version_num)
        
        return max_version
    
    async def _archive_previous_version(self, db: Session, previous_doc: Document, new_version: int):
        """Mark previous version as archived"""
        
        metadata = previous_doc.metadata or {}
        metadata.update({
            'archived_at': datetime.utcnow().isoformat(),
            'archived_by_version': new_version,
            'is_current': False
        })
        
        await document_crud.update(
            db, db_obj=previous_doc, obj_in={'metadata': metadata}
        )
    
    async def get_document_history(
        self,
        db: Session,
        document_id: str,
        tpa_id: str
    ) -> List[DocumentVersion]:
        """Get complete version history for a document"""
        
        try:
            # Find original document
            original_doc = await document_crud.get(db, id=document_id, tpa_id=tpa_id)
            if not original_doc:
                raise DocumentProcessingError("Document not found")
            
            # Get original document ID (might be a version itself)
            original_doc_id = document_id
            metadata = original_doc.metadata or {}
            if metadata.get('original_document_id'):
                original_doc_id = metadata['original_document_id']
            
            # Find all versions
            versions_query = db.query(Document).filter(
                and_(
                    Document.tpa_id == tpa_id,
                    Document.metadata['original_document_id'].astext == original_doc_id
                )
            ).order_by(desc(Document.created_at))
            
            version_docs = versions_query.all()
            
            # Include original document if not already included
            if not any(doc.id == original_doc_id for doc in version_docs):
                original = await document_crud.get(db, id=original_doc_id, tpa_id=tpa_id)
                if original:
                    version_docs.append(original)
            
            # Convert to DocumentVersion objects
            versions = [DocumentVersion(doc) for doc in version_docs]
            
            # Sort by version number
            versions.sort(key=lambda v: v.version_number, reverse=True)
            
            return versions
            
        except Exception as e:
            self.logger.error(f"Failed to get document history: {e}")
            raise DocumentProcessingError(f"Failed to get document history: {e}")
    
    async def _generate_change_summary(
        self,
        db: Session,
        old_document: Document,
        new_document: Document,
        tpa_id: str
    ) -> Dict[str, Any]:
        """Generate summary of changes between document versions"""
        
        try:
            change_summary = {
                'file_size_change': new_document.file_size - old_document.file_size,
                'hash_changed': old_document.file_hash != new_document.file_hash,
                'content_analysis': {},
                'metadata_changes': {}
            }
            
            # Analyze filename changes
            if old_document.filename != new_document.filename:
                change_summary['filename_changed'] = {
                    'old': old_document.filename,
                    'new': new_document.filename
                }
            
            # Compare metadata
            old_metadata = old_document.metadata or {}
            new_metadata = new_document.metadata or {}
            
            # Exclude version-specific metadata from comparison
            exclude_keys = {
                'version_number', 'original_document_id', 'previous_version',
                'uploaded_at', 'uploaded_by', 'is_version', 'change_notes'
            }
            
            old_comparable = {k: v for k, v in old_metadata.items() if k not in exclude_keys}
            new_comparable = {k: v for k, v in new_metadata.items() if k not in exclude_keys}
            
            if old_comparable != new_comparable:
                change_summary['metadata_changes'] = {
                    'added': {k: v for k, v in new_comparable.items() if k not in old_comparable},
                    'removed': {k: v for k, v in old_comparable.items() if k not in new_comparable},
                    'modified': {
                        k: {'old': old_comparable[k], 'new': new_comparable[k]}
                        for k in old_comparable
                        if k in new_comparable and old_comparable[k] != new_comparable[k]
                    }
                }
            
            # Try to analyze content changes for text-based documents
            if old_document.document_type in [DocumentType.SPD, DocumentType.OTHER]:
                content_diff = await self._analyze_content_changes(old_document, new_document)
                if content_diff:
                    change_summary['content_analysis'] = content_diff
            
            return change_summary
            
        except Exception as e:
            self.logger.warning(f"Failed to generate change summary: {e}")
            return {'error': 'Could not generate change summary'}
    
    async def _analyze_content_changes(
        self,
        old_document: Document,
        new_document: Document
    ) -> Optional[Dict[str, Any]]:
        """Analyze content changes between documents"""
        
        try:
            # For PDF documents, we'd need to extract text first
            # This is a simplified version - in production you'd want more sophisticated analysis
            
            # Get document chunks for comparison
            old_chunks = old_document.chunks if hasattr(old_document, 'chunks') else []
            new_chunks = new_document.chunks if hasattr(new_document, 'chunks') else []
            
            if not old_chunks or not new_chunks:
                return None
            
            # Simple chunk count comparison
            old_chunk_count = len(old_chunks)
            new_chunk_count = len(new_chunks)
            
            content_analysis = {
                'chunk_count_change': new_chunk_count - old_chunk_count,
                'estimated_content_change': 'moderate'  # Simplified
            }
            
            # Estimate change magnitude
            change_ratio = abs(new_chunk_count - old_chunk_count) / max(old_chunk_count, 1)
            
            if change_ratio < 0.1:
                content_analysis['estimated_content_change'] = 'minimal'
            elif change_ratio < 0.3:
                content_analysis['estimated_content_change'] = 'moderate'
            else:
                content_analysis['estimated_content_change'] = 'significant'
            
            return content_analysis
            
        except Exception as e:
            self.logger.warning(f"Content analysis failed: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def compare_versions(
        self,
        db: Session,
        version1_id: str,
        version2_id: str,
        tpa_id: str
    ) -> Dict[str, Any]:
        """Compare two specific versions of a document"""
        
        try:
            # Get both documents
            doc1 = await document_crud.get(db, id=version1_id, tpa_id=tpa_id)
            doc2 = await document_crud.get(db, id=version2_id, tpa_id=tpa_id)
            
            if not doc1 or not doc2:
                raise DocumentProcessingError("One or both documents not found")
            
            # Generate comparison
            comparison = {
                'version1': {
                    'id': doc1.id,
                    'version': doc1.metadata.get('version_number', 1) if doc1.metadata else 1,
                    'filename': doc1.filename,
                    'file_size': doc1.file_size,
                    'created_at': doc1.created_at.isoformat()
                },
                'version2': {
                    'id': doc2.id,
                    'version': doc2.metadata.get('version_number', 1) if doc2.metadata else 1,
                    'filename': doc2.filename,
                    'file_size': doc2.file_size,
                    'created_at': doc2.created_at.isoformat()
                },
                'differences': await self._generate_change_summary(db, doc1, doc2, tpa_id)
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Failed to compare versions: {e}")
            raise DocumentProcessingError(f"Failed to compare versions: {e}")
    
    async def rollback_to_version(
        self,
        db: Session,
        target_version_id: str,
        tpa_id: str,
        user_id: str,
        rollback_reason: str
    ) -> Document:
        """Rollback to a previous version by creating a new version based on the target"""
        
        try:
            # Get target version
            target_doc = await document_crud.get(db, id=target_version_id, tpa_id=tpa_id)
            if not target_doc:
                raise DocumentProcessingError("Target version not found")
            
            # Get original document ID
            original_doc_id = target_version_id
            if target_doc.metadata and target_doc.metadata.get('original_document_id'):
                original_doc_id = target_doc.metadata['original_document_id']
            
            # Get current version number
            current_version = self._get_current_version_number(db, original_doc_id, tpa_id)
            new_version = current_version + 1
            
            # Create rollback version
            rollback_data = {
                'filename': target_doc.filename,
                'file_path': target_doc.file_path,  # Copy file if needed
                'file_size': target_doc.file_size,
                'file_hash': target_doc.file_hash,
                'document_type': target_doc.document_type,
                'health_plan_id': target_doc.health_plan_id,
                'processing_status': 'completed',  # Assume processed since rolling back
                'metadata': {
                    **target_doc.metadata,
                    'version_number': new_version,
                    'original_document_id': original_doc_id,
                    'rollback_to_version': target_doc.metadata.get('version_number', 1) if target_doc.metadata else 1,
                    'rollback_reason': rollback_reason,
                    'rollback_by': user_id,
                    'rollback_at': datetime.utcnow().isoformat(),
                    'is_rollback': True
                }
            }
            
            # Create rollback document
            rollback_doc = await document_crud.create(db, obj_in=rollback_data, tpa_id=tpa_id)
            
            # Track rollback analytics
            await analytics_service.track_document_access(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                document_id=rollback_doc.id
            )
            
            self.logger.info(f"Rolled back to version {target_version_id} as new version {new_version}")
            
            return rollback_doc
            
        except Exception as e:
            self.logger.error(f"Failed to rollback to version: {e}")
            raise DocumentProcessingError(f"Failed to rollback to version: {e}")
    
    async def delete_version(
        self,
        db: Session,
        version_id: str,
        tpa_id: str,
        user_id: str,
        delete_reason: str
    ) -> bool:
        """Delete a specific version (soft delete)"""
        
        try:
            # Get version
            version_doc = await document_crud.get(db, id=version_id, tpa_id=tpa_id)
            if not version_doc:
                raise DocumentProcessingError("Version not found")
            
            # Prevent deletion of current/active versions
            metadata = version_doc.metadata or {}
            if not metadata.get('is_version', False):
                raise DocumentProcessingError("Cannot delete original document through version control")
            
            # Soft delete by updating metadata
            metadata.update({
                'deleted': True,
                'deleted_by': user_id,
                'deleted_at': datetime.utcnow().isoformat(),
                'delete_reason': delete_reason
            })
            
            await document_crud.update(
                db, db_obj=version_doc, obj_in={'metadata': metadata}
            )
            
            self.logger.info(f"Deleted version {version_id} by user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete version: {e}")
            raise DocumentProcessingError(f"Failed to delete version: {e}")


# Create version control service instance
document_version_control = DocumentVersionControl()