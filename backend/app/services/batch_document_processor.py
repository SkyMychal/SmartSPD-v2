"""
Batch document processing service for handling multiple documents concurrently
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import tempfile
import shutil
import zipfile
import os

from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError
from app.models.document import Document, ProcessingStatus, DocumentType
from app.services.document_processor import DocumentProcessor
from app.services.analytics_service import analytics_service
from app.crud.document import document_crud

logger = logging.getLogger(__name__)


class BatchDocumentProcessor:
    """Service for processing multiple documents in batches"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.max_concurrent = getattr(settings, 'MAX_CONCURRENT_PROCESSING', 5)
        self.max_batch_size = getattr(settings, 'MAX_BATCH_SIZE', 20)
    
    async def process_batch(
        self,
        db: Session,
        file_paths: List[str],
        tpa_id: str,
        health_plan_id: Optional[str] = None,
        user_id: Optional[str] = None,
        batch_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a batch of documents concurrently"""
        
        if len(file_paths) > self.max_batch_size:
            raise DocumentProcessingError(
                f"Batch size {len(file_paths)} exceeds maximum of {self.max_batch_size}"
            )
        
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting batch processing {batch_id} with {len(file_paths)} documents")
        
        # Create document records first
        documents = []
        for file_path in file_paths:
            try:
                document = await self._create_document_record(
                    db, file_path, tpa_id, health_plan_id, batch_id, batch_metadata
                )
                documents.append((document, file_path))
            except Exception as e:
                logger.error(f"Failed to create document record for {file_path}: {e}")
                continue
        
        # Process documents in parallel with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        
        for document, file_path in documents:
            task = self._process_single_document_with_semaphore(
                semaphore, db, document, file_path, user_id
            )
            tasks.append(task)
        
        # Wait for all processing to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile batch results
        batch_results = {
            'batch_id': batch_id,
            'total_documents': len(documents),
            'successful': 0,
            'failed': 0,
            'results': [],
            'processing_time': 0,
            'started_at': datetime.utcnow().isoformat()
        }
        
        start_time = datetime.utcnow()
        
        for i, result in enumerate(results):
            document, file_path = documents[i]
            
            if isinstance(result, Exception):
                logger.error(f"Document processing failed for {document.id}: {result}")
                document.processing_status = ProcessingStatus.FAILED
                document.error_message = str(result)
                batch_results['failed'] += 1
                
                batch_results['results'].append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'status': 'failed',
                    'error': str(result)
                })
            elif result:
                document.processing_status = ProcessingStatus.COMPLETED
                batch_results['successful'] += 1
                
                batch_results['results'].append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'status': 'completed'
                })
            else:
                document.processing_status = ProcessingStatus.FAILED
                document.error_message = "Processing returned False"
                batch_results['failed'] += 1
                
                batch_results['results'].append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'status': 'failed',
                    'error': 'Processing returned False'
                })
            
            db.commit()
        
        batch_results['processing_time'] = (datetime.utcnow() - start_time).total_seconds()
        
        # Track batch analytics
        if user_id:
            await analytics_service.track_document_access(
                db=db,
                user_id=user_id,
                tpa_id=tpa_id,
                document_id=batch_id  # Use batch_id as document_id for batch tracking
            )
        
        logger.info(
            f"Batch {batch_id} completed: {batch_results['successful']} successful, "
            f"{batch_results['failed']} failed in {batch_results['processing_time']:.2f}s"
        )
        
        return batch_results
    
    async def _process_single_document_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        db: Session,
        document: Document,
        file_path: str,
        user_id: Optional[str]
    ) -> bool:
        """Process a single document with concurrency limiting"""
        
        async with semaphore:
            try:
                logger.info(f"Processing document {document.id}: {document.filename}")
                result = await self.document_processor.process_document(db, document, file_path)
                
                if result and user_id:
                    # Track individual document processing
                    await analytics_service.track_document_access(
                        db=db,
                        user_id=user_id,
                        tpa_id=document.tpa_id,
                        document_id=document.id
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to process document {document.id}: {e}")
                raise
    
    async def _create_document_record(
        self,
        db: Session,
        file_path: str,
        tpa_id: str,
        health_plan_id: Optional[str],
        batch_id: str,
        batch_metadata: Optional[Dict[str, Any]]
    ) -> Document:
        """Create document record for file"""
        
        path = Path(file_path)
        filename = path.name
        file_size = path.stat().st_size
        
        # Detect document type
        document_type = self._detect_document_type(filename)
        
        # Calculate file hash
        import hashlib
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Create document record
        document_data = {
            'filename': filename,
            'file_path': str(path),
            'file_size': file_size,
            'file_hash': file_hash,
            'document_type': document_type,
            'processing_status': ProcessingStatus.PENDING,
            'health_plan_id': health_plan_id,
            'metadata': {
                'batch_id': batch_id,
                'batch_metadata': batch_metadata or {},
                'uploaded_at': datetime.utcnow().isoformat()
            }
        }
        
        document = await document_crud.create(db, obj_in=document_data, tpa_id=tpa_id)
        return document
    
    def _detect_document_type(self, filename: str) -> DocumentType:
        """Detect document type from filename"""
        
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            # Check for SPD indicators
            if any(indicator in filename_lower for indicator in ['spd', 'summary', 'plan', 'description']):
                return DocumentType.SPD
            else:
                return DocumentType.OTHER
        elif filename_lower.endswith(('.xlsx', '.xls')):
            # Check for BPS indicators
            if any(indicator in filename_lower for indicator in ['bps', 'benefit', 'schedule']):
                return DocumentType.BPS
            else:
                return DocumentType.OTHER
        else:
            return DocumentType.OTHER
    
    async def process_zip_archive(
        self,
        db: Session,
        zip_path: str,
        tpa_id: str,
        health_plan_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extract_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process all documents in a ZIP archive"""
        
        try:
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP file
                extracted_files = await self._extract_zip_file(zip_path, temp_dir)
                
                if not extracted_files:
                    raise DocumentProcessingError("No valid documents found in ZIP archive")
                
                # Process extracted files as batch
                batch_metadata = {
                    'source': 'zip_archive',
                    'original_filename': Path(zip_path).name,
                    'extract_metadata': extract_metadata or {}
                }
                
                result = await self.process_batch(
                    db=db,
                    file_paths=extracted_files,
                    tpa_id=tpa_id,
                    health_plan_id=health_plan_id,
                    user_id=user_id,
                    batch_metadata=batch_metadata
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to process ZIP archive {zip_path}: {e}")
            raise DocumentProcessingError(f"Failed to process ZIP archive: {e}")
    
    async def _extract_zip_file(self, zip_path: str, extract_dir: str) -> List[str]:
        """Extract ZIP file and return list of document files"""
        
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(extract_dir)
                
                # Find document files
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Filter for supported document types
                        if self._is_supported_document(file):
                            extracted_files.append(file_path)
                            
        except Exception as e:
            logger.error(f"Failed to extract ZIP file {zip_path}: {e}")
            raise
        
        return extracted_files
    
    def _is_supported_document(self, filename: str) -> bool:
        """Check if file is a supported document type"""
        
        supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.txt']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    async def get_batch_status(
        self,
        db: Session,
        batch_id: str,
        tpa_id: str
    ) -> Dict[str, Any]:
        """Get status of a batch processing job"""
        
        try:
            # Find documents in this batch
            documents = await document_crud.get_by_batch(db, batch_id=batch_id, tpa_id=tpa_id)
            
            if not documents:
                return {'error': 'Batch not found'}
            
            # Compile status
            status_counts = {}
            for doc in documents:
                status = doc.processing_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            batch_status = {
                'batch_id': batch_id,
                'total_documents': len(documents),
                'status_breakdown': status_counts,
                'documents': [
                    {
                        'id': doc.id,
                        'filename': doc.filename,
                        'status': doc.processing_status.value,
                        'error_message': doc.error_message,
                        'created_at': doc.created_at.isoformat(),
                        'updated_at': doc.updated_at.isoformat()
                    }
                    for doc in documents
                ]
            }
            
            return batch_status
            
        except Exception as e:
            logger.error(f"Failed to get batch status for {batch_id}: {e}")
            return {'error': str(e)}
    
    async def retry_failed_documents(
        self,
        db: Session,
        batch_id: str,
        tpa_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retry processing failed documents in a batch"""
        
        try:
            # Find failed documents in this batch
            failed_docs = await document_crud.get_failed_by_batch(
                db, batch_id=batch_id, tpa_id=tpa_id
            )
            
            if not failed_docs:
                return {'message': 'No failed documents to retry', 'retried': 0}
            
            retry_count = 0
            retry_results = []
            
            for doc in failed_docs:
                try:
                    # Reset status to pending
                    doc.processing_status = ProcessingStatus.PENDING
                    doc.error_message = None
                    db.commit()
                    
                    # Attempt reprocessing
                    success = await self.document_processor.process_document(
                        db, doc, doc.file_path
                    )
                    
                    if success:
                        doc.processing_status = ProcessingStatus.COMPLETED
                        retry_count += 1
                        retry_results.append({
                            'document_id': doc.id,
                            'filename': doc.filename,
                            'status': 'success'
                        })
                    else:
                        doc.processing_status = ProcessingStatus.FAILED
                        doc.error_message = "Retry processing failed"
                        retry_results.append({
                            'document_id': doc.id,
                            'filename': doc.filename,
                            'status': 'failed',
                            'error': 'Retry processing failed'
                        })
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to retry document {doc.id}: {e}")
                    doc.processing_status = ProcessingStatus.FAILED
                    doc.error_message = f"Retry failed: {e}"
                    db.commit()
                    
                    retry_results.append({
                        'document_id': doc.id,
                        'filename': doc.filename,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'message': f'Retried {len(failed_docs)} documents',
                'successful_retries': retry_count,
                'failed_retries': len(failed_docs) - retry_count,
                'results': retry_results
            }
            
        except Exception as e:
            logger.error(f"Failed to retry batch {batch_id}: {e}")
            raise DocumentProcessingError(f"Failed to retry batch: {e}")


# Create batch processor instance
batch_document_processor = BatchDocumentProcessor()