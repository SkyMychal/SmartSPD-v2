"""
Document processing service for SPD PDFs and BPS Excel files
"""
import os
import uuid
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber
from pdfplumber.pdf import PDF
from pdfplumber.page import Page
import openai
import logging
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, AIServiceError
from app.models.document import Document, DocumentChunk, DocumentType, ProcessingStatus
from app.services.vector_service import VectorService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.ai_service import ai_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processing service"""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.kg_service = KnowledgeGraphService()
        self.ai_service = ai_service
        openai.api_key = settings.OPENAI_API_KEY
    
    async def process_document(
        self, 
        db: Session,
        document: Document,
        file_path: str
    ) -> bool:
        """Process uploaded document based on type"""
        try:
            # Initialize vector service if not already initialized
            if not self.vector_service.initialized:
                await self.vector_service.initialize()
                logger.info("🔥 Vector service initialized for document processing")
            
            # Update processing status
            document.processing_status = ProcessingStatus.PROCESSING
            db.commit()
            
            if document.document_type == DocumentType.SPD:
                success = await self._process_spd_pdf(db, document, file_path)
            elif document.document_type == DocumentType.BPS:
                success = await self._process_bps_excel(db, document, file_path)
            else:
                success = await self._process_generic_document(db, document, file_path)
            
            # Update final status
            if success:
                document.processing_status = ProcessingStatus.COMPLETED
                logger.info(f"Document {document.id} processed successfully")
            else:
                document.processing_status = ProcessingStatus.FAILED
                logger.error(f"Document {document.id} processing failed")
            
            db.commit()
            return success
            
        except Exception as e:
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = str(e)
            db.commit()
            logger.error(f"Document processing failed: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
    
    async def _process_spd_pdf(
        self, 
        db: Session, 
        document: Document, 
        file_path: str
    ) -> bool:
        """Process SPD PDF document with enhanced AI-powered extraction and detailed tracking"""
        try:
            logger.info(f"🔍 Starting SPD PDF processing for: {document.original_filename}")
            spd_processor = SPDProcessor(self.ai_service)
            
            # Extract structured content with document type specialization
            logger.info("📄 Extracting content from PDF...")
            extracted_data = await spd_processor.extract_spd_content(file_path)
            
            # Store extracted metadata
            document.extracted_metadata = extracted_data.get('metadata', {})
            document.page_count = extracted_data.get('page_count', 0)
            logger.info(f"📊 Extracted metadata - Pages: {document.page_count}, Sections: {len(extracted_data.get('metadata', {}).get('sections', []))}")
            
            # Create document chunks with enhanced processing
            chunks = extracted_data.get('chunks', [])
            logger.info(f"🧩 Processing {len(chunks)} content chunks for RAG...")
            chunk_objects = []
            
            for i, chunk_data in enumerate(chunks):
                # Log progress every 10 chunks
                if i % 10 == 0:
                    logger.info(f"📝 Processing chunk {i+1}/{len(chunks)} - {chunk_data.get('section_title', 'Content')}")
                
                chunk = DocumentChunk(
                    tpa_id=document.tpa_id,
                    document_id=document.id,
                    content=chunk_data['content'],
                    content_hash=self._calculate_hash(chunk_data['content']),
                    chunk_index=i,
                    page_number=chunk_data.get('page_number'),
                    section_title=chunk_data.get('section_title'),
                    chunk_type=chunk_data.get('chunk_type', 'paragraph'),
                    keywords=chunk_data.get('keywords', []),
                    entities=chunk_data.get('entities', []),
                    topics=chunk_data.get('topics', []),
                    relevance_score=chunk_data.get('relevance_score', 0.5),
                    confidence_score=chunk_data.get('confidence_score', 0.5)
                )
                
                # Embeddings will be generated after chunks are saved to get IDs
                
                chunk_objects.append(chunk)
                db.add(chunk)
            
            # Flush to database to get chunk IDs, then process embeddings
            db.flush()
            logger.info(f"💾 Saved {len(chunk_objects)} chunks to database, now generating embeddings...")
            
            # Initialize embedding counters
            vectorized_chunks = 0
            failed_chunks = 0
            
            # Now generate embeddings for chunks that don't have them yet
            for i, (chunk, chunk_data) in enumerate(zip(chunk_objects, chunks)):
                if not chunk.embedding:  # Skip if already has embedding
                    try:
                        logger.info(f"🧠 Generating embedding for chunk {i+1}/{len(chunks)}")
                        embedding = await self.vector_service.generate_embedding(chunk_data['content'])
                        chunk.embedding = embedding
                        chunk.embedding_model = "text-embedding-ada-002"
                        vectorized_chunks += 1
                        
                        # Store in vector database using the chunk ID
                        await self.vector_service.upsert_document_chunk(
                            chunk_id=chunk.id,
                            text=chunk_data['content'],
                            metadata={
                                'tpa_id': document.tpa_id,
                                'document_id': document.id,
                                'document_type': document.document_type.value,
                                'health_plan_id': document.health_plan_id,
                                'chunk_index': i,
                                'page_number': chunk_data.get('page_number'),
                                'section_title': chunk_data.get('section_title'),
                                'chunk_type': chunk_data.get('chunk_type')
                            }
                        )
                        logger.info(f"✅ Chunk {i+1} embedded and stored in vector database")
                    except Exception as e:
                        logger.error(f"❌ Failed to generate embedding for chunk {i}: {e}")
                        failed_chunks += 1
            
            # Log chunking summary
            logger.info(f"✅ SPD Chunking Complete - Total: {len(chunks)}, Vectorized: {vectorized_chunks}, Failed: {failed_chunks}")
            
            # Extract benefits and store in knowledge graph
            if extracted_data.get('benefits'):
                logger.info(f"🔗 Storing {len(extracted_data['benefits'])} benefits in knowledge graph...")
                await self._store_benefits_in_kg(document, extracted_data['benefits'])
                logger.info("✅ Knowledge graph storage complete")
            
            db.commit()
            logger.info(f"🎉 SPD Processing Complete for: {document.original_filename}")
            return True
            
        except Exception as e:
            logger.error(f"SPD processing failed: {e}")
            return False
    
    async def _process_bps_excel(
        self, 
        db: Session, 
        document: Document, 
        file_path: str
    ) -> bool:
        """Process BPS Excel file with enhanced AI-powered benefit extraction and knowledge graph tracking"""
        try:
            logger.info(f"📊 Starting BPS Excel processing for: {document.original_filename}")
            bps_processor = BPSProcessor(self.ai_service)
            
            # Extract benefit data with document type specialization
            logger.info("📋 Extracting structured benefit data from Excel...")
            extracted_data = await bps_processor.extract_bps_data(file_path)
            
            # Store extracted metadata
            document.extracted_metadata = extracted_data.get('metadata', {})
            logger.info(f"📊 Extracted metadata - Sheets: {len(extracted_data.get('metadata', {}).get('sheets', []))}, Benefits: {len(extracted_data.get('benefits', []))}")
            
            # Create summary chunks
            chunks = extracted_data.get('chunks', [])
            logger.info(f"📝 Creating {len(chunks)} summary chunks...")
            vectorized_chunks = 0
            failed_chunks = 0
            
            for i, chunk_data in enumerate(chunks):
                chunk = DocumentChunk(
                    tpa_id=document.tpa_id,
                    document_id=document.id,
                    content=chunk_data['content'],
                    content_hash=self._calculate_hash(chunk_data['content']),
                    chunk_index=i,
                    section_title=chunk_data.get('section_title'),
                    chunk_type=chunk_data.get('chunk_type', 'benefit_summary'),
                    keywords=chunk_data.get('keywords', []),
                    relevance_score=chunk_data.get('relevance_score', 0.8),
                    confidence_score=chunk_data.get('confidence_score', 0.9)
                )
                
                # Generate embedding
                if self.vector_service.initialized:
                    try:
                        embedding = await self.vector_service.generate_embedding(chunk_data['content'])
                        chunk.embedding = embedding
                        chunk.embedding_model = "text-embedding-ada-002"
                        vectorized_chunks += 1
                        
                        # Store in vector database
                        await self.vector_service.upsert_document_chunk(
                            chunk_id=chunk.id,
                            text=chunk_data['content'],
                            metadata={
                                'tpa_id': document.tpa_id,
                                'document_id': document.id,
                                'document_type': document.document_type.value,
                                'health_plan_id': document.health_plan_id,
                                'chunk_index': i,
                                'chunk_type': chunk_data.get('chunk_type')
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for BPS chunk {i}: {e}")
                        failed_chunks += 1
                else:
                    logger.warning(f"Vector service not initialized, skipping embedding for BPS chunk {i}")
                    failed_chunks += 1
                
                db.add(chunk)
            
            logger.info(f"✅ BPS Chunking Complete - Total: {len(chunks)}, Vectorized: {vectorized_chunks}, Failed: {failed_chunks}")
            
            # Store benefits in knowledge graph
            benefits_count = 0
            if extracted_data.get('benefits'):
                benefits_count = len(extracted_data['benefits'])
                logger.info(f"🕸️ Building knowledge graph with {benefits_count} benefit relationships...")
                await self._store_benefits_in_kg(document, extracted_data['benefits'])
                logger.info("✅ Knowledge graph construction complete")
            
            # Update health plan with BPS data
            if document.health_plan_id and extracted_data.get('plan_data'):
                logger.info(f"💾 Updating health plan database with structured benefit data...")
                await self._update_health_plan_from_bps(db, document.health_plan_id, extracted_data['plan_data'])
                logger.info("✅ Health plan update complete")
            
            db.commit()
            logger.info(f"🎉 BPS Processing Complete for: {document.original_filename} - {benefits_count} benefits stored")
            return True
            
        except Exception as e:
            logger.error(f"BPS processing failed: {e}")
            return False
    
    async def _process_generic_document(
        self, 
        db: Session, 
        document: Document, 
        file_path: str
    ) -> bool:
        """Process generic documents with basic text extraction"""
        try:
            # Basic text extraction
            if file_path.lower().endswith('.pdf'):
                content = await self._extract_pdf_text(file_path)
            else:
                # Handle other document types
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Create single chunk for generic documents
            chunk = DocumentChunk(
                tpa_id=document.tpa_id,
                document_id=document.id,
                content=content,
                content_hash=self._calculate_hash(content),
                chunk_index=0,
                chunk_type='document',
                relevance_score=0.5,
                confidence_score=0.5
            )
            
            db.add(chunk)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Generic document processing failed: {e}")
            return False
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise DocumentProcessingError(f"Failed to extract PDF text: {e}")
        
        return text
    
    async def _store_benefits_in_kg(self, document: Document, benefits: List[Dict[str, Any]]):
        """Store extracted benefits in knowledge graph"""
        if not self.kg_service.initialized:
            return
        
        try:
            # Create benefit nodes
            await self.kg_service.create_benefit_nodes(benefits)
            logger.info(f"Stored {len(benefits)} benefits in knowledge graph")
        except Exception as e:
            logger.warning(f"Failed to store benefits in knowledge graph: {e}")
    
    async def _update_health_plan_from_bps(
        self, 
        db: Session, 
        health_plan_id: str, 
        plan_data: Dict[str, Any]
    ):
        """Update health plan with data from BPS"""
        try:
            from app.crud.health_plan import health_plan_crud
            
            health_plan = await health_plan_crud.get(db, id=health_plan_id)
            if health_plan:
                # Update health plan fields from BPS data
                update_data = {}
                
                # Map BPS fields to health plan fields
                field_mapping = {
                    'deductible_individual': 'deductible_individual',
                    'deductible_family': 'deductible_family',
                    'out_of_pocket_max_individual': 'out_of_pocket_max_individual',
                    'out_of_pocket_max_family': 'out_of_pocket_max_family',
                    'primary_care_copay': 'primary_care_copay',
                    'specialist_copay': 'specialist_copay',
                    'urgent_care_copay': 'urgent_care_copay',
                    'emergency_room_copay': 'emergency_room_copay',
                    'in_network_coinsurance': 'in_network_coinsurance',
                    'out_of_network_coinsurance': 'out_of_network_coinsurance',
                    'rx_generic_copay': 'rx_generic_copay',
                    'rx_brand_copay': 'rx_brand_copay',
                    'rx_specialty_copay': 'rx_specialty_copay'
                }
                
                for bps_field, plan_field in field_mapping.items():
                    if bps_field in plan_data and plan_data[bps_field] is not None:
                        update_data[plan_field] = plan_data[bps_field]
                
                # Update benefits summary
                if plan_data.get('benefits_summary'):
                    update_data['benefits_summary'] = plan_data['benefits_summary']
                
                if update_data:
                    await health_plan_crud.update(db, db_obj=health_plan, obj_in=update_data)
                    logger.info(f"Updated health plan {health_plan_id} with BPS data")
        
        except Exception as e:
            logger.warning(f"Failed to update health plan from BPS: {e}")
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

class SPDProcessor:
    """Specialized processor for SPD PDF documents with AI enhancement"""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
    
    async def extract_spd_content(self, file_path: str) -> Dict[str, Any]:
        """Extract structured content from SPD PDF"""
        try:
            with pdfplumber.open(file_path) as pdf:
                extracted_data = {
                    'metadata': {},
                    'chunks': [],
                    'benefits': [],
                    'page_count': len(pdf.pages)
                }
                
                # Extract metadata from first page
                if pdf.pages:
                    extracted_data['metadata'] = await self._extract_spd_metadata(pdf.pages[0])
                
                # Process each page
                current_section = None
                for page_num, page in enumerate(pdf.pages):
                    page_content = await self._process_spd_page(page, page_num + 1)
                    
                    # Detect section headers
                    if page_content.get('section_title'):
                        current_section = page_content['section_title']
                    
                    # Add page content as chunks
                    for chunk in page_content.get('chunks', []):
                        chunk['section_title'] = current_section
                        chunk['page_number'] = page_num + 1
                        extracted_data['chunks'].append(chunk)
                    
                    # Extract benefits from this page
                    page_benefits = await self._extract_benefits_from_page(page, page_num + 1)
                    extracted_data['benefits'].extend(page_benefits)
                
                # Enhance chunks with AI analysis
                if settings.OPENAI_API_KEY:
                    await self._enhance_chunks_with_ai(extracted_data['chunks'])
                
                return extracted_data
                
        except Exception as e:
            logger.error(f"SPD content extraction failed: {e}")
            raise DocumentProcessingError(f"Failed to extract SPD content: {e}")
    
    async def _extract_spd_metadata(self, first_page: Page) -> Dict[str, Any]:
        """Extract metadata from SPD first page"""
        try:
            text = first_page.extract_text() or ""
            
            metadata = {
                'title': None,
                'plan_name': None,
                'effective_date': None,
                'plan_sponsor': None,
                'administrator': None
            }
            
            # Extract title (usually the largest text or first line)
            lines = text.split('\n')
            if lines:
                metadata['title'] = lines[0].strip()
            
            # Use AI to extract structured metadata
            if settings.OPENAI_API_KEY:
                ai_metadata = await self._extract_metadata_with_ai(text[:2000])
                metadata.update(ai_metadata)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract SPD metadata: {e}")
            return {}
    
    async def _process_spd_page(self, page: Page, page_num: int) -> Dict[str, Any]:
        """Process individual SPD page"""
        try:
            text = page.extract_text() or ""
            
            # Extract tables if present
            tables = page.extract_tables()
            
            page_content = {
                'chunks': [],
                'section_title': None,
                'tables': []
            }
            
            # Detect section headers (usually larger font or all caps)
            section_title = self._detect_section_header(text)
            if section_title:
                page_content['section_title'] = section_title
            
            # Split text into logical chunks
            chunks = self._split_into_chunks(text, page_num)
            page_content['chunks'] = chunks
            
            # Process tables
            if tables:
                for i, table in enumerate(tables):
                    table_content = self._process_table(table, page_num, i)
                    if table_content:
                        page_content['chunks'].append({
                            'content': table_content,
                            'chunk_type': 'table',
                            'page_number': page_num,
                            'table_index': i
                        })
            
            return page_content
            
        except Exception as e:
            logger.warning(f"Failed to process SPD page {page_num}: {e}")
            return {'chunks': [], 'section_title': None, 'tables': []}
    
    def _detect_section_header(self, text: str) -> Optional[str]:
        """Detect section headers in text"""
        lines = text.split('\n')
        
        # Look for common section header patterns
        header_patterns = [
            'SECTION',
            'PART',
            'CHAPTER',
            'SUMMARY OF BENEFITS',
            'COVERAGE',
            'BENEFITS',
            'EXCLUSIONS',
            'LIMITATIONS'
        ]
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip().upper()
            if any(pattern in line for pattern in header_patterns):
                if len(line) < 100:  # Headers are usually short
                    return line.title()
        
        return None
    
    def _split_into_chunks(self, text: str, page_num: int, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Split text into semantic chunks"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        current_keywords = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed max size, save current chunk
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'chunk_type': 'paragraph',
                    'keywords': current_keywords,
                    'relevance_score': self._calculate_relevance_score(current_chunk)
                })
                current_chunk = ""
                current_keywords = []
            
            current_chunk += paragraph + "\n\n"
            
            # Extract keywords from paragraph
            paragraph_keywords = self._extract_keywords(paragraph)
            current_keywords.extend(paragraph_keywords)
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'chunk_type': 'paragraph',
                'keywords': list(set(current_keywords)),
                'relevance_score': self._calculate_relevance_score(current_chunk)
            })
        
        return chunks
    
    def _process_table(self, table: List[List[str]], page_num: int, table_index: int) -> Optional[str]:
        """Process extracted table into readable text"""
        try:
            if not table or not table[0]:
                return None
            
            # Convert table to text format
            table_text = "Table:\n"
            
            # Add headers if present
            if table[0]:
                headers = [cell or "" for cell in table[0]]
                table_text += " | ".join(headers) + "\n"
                table_text += "-" * len(" | ".join(headers)) + "\n"
            
            # Add data rows
            for row in table[1:]:
                if row:
                    row_data = [cell or "" for cell in row]
                    table_text += " | ".join(row_data) + "\n"
            
            return table_text
            
        except Exception as e:
            logger.warning(f"Failed to process table {table_index} on page {page_num}: {e}")
            return None
    
    async def _extract_benefits_from_page(self, page: Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract benefit information from page"""
        try:
            text = page.extract_text() or ""
            benefits = []
            
            # Look for benefit patterns
            benefit_patterns = [
                r'(\$\d+(?:,\d{3})*(?:\.\d{2})?)',  # Dollar amounts
                r'(\d+%)',  # Percentages
                r'(copay|coinsurance|deductible|out-of-pocket)',  # Benefit terms
            ]
            
            # Extract tables which often contain benefit information
            tables = page.extract_tables()
            for table in tables:
                table_benefits = self._extract_benefits_from_table(table, page_num)
                benefits.extend(table_benefits)
            
            return benefits
            
        except Exception as e:
            logger.warning(f"Failed to extract benefits from page {page_num}: {e}")
            return []
    
    def _extract_benefits_from_table(self, table: List[List[str]], page_num: int) -> List[Dict[str, Any]]:
        """Extract benefit data from table structure"""
        benefits = []
        
        try:
            if not table or len(table) < 2:
                return benefits
            
            headers = [cell.lower().strip() if cell else "" for cell in table[0]]
            
            for row_index, row in enumerate(table[1:], 1):
                if not row:
                    continue
                
                benefit_data = {}
                for col_index, cell in enumerate(row):
                    if col_index < len(headers) and cell:
                        header = headers[col_index]
                        benefit_data[header] = cell.strip()
                
                if benefit_data:
                    benefits.append({
                        'id': str(uuid.uuid4()),
                        'benefit_type': self._classify_benefit_type(benefit_data),
                        'category': self._categorize_benefit(benefit_data),
                        'description': self._generate_benefit_description(benefit_data),
                        'data': benefit_data,
                        'page_number': page_num,
                        'table_row': row_index,
                        'created_at': datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            logger.warning(f"Failed to extract benefits from table: {e}")
        
        return benefits
    
    def _classify_benefit_type(self, benefit_data: Dict[str, str]) -> str:
        """Classify the type of benefit"""
        data_str = ' '.join(benefit_data.values()).lower()
        
        if any(term in data_str for term in ['deductible', 'annual deductible']):
            return 'deductible'
        elif any(term in data_str for term in ['copay', 'co-pay', 'copayment']):
            return 'copay'
        elif any(term in data_str for term in ['coinsurance', 'co-insurance']):
            return 'coinsurance'
        elif any(term in data_str for term in ['out-of-pocket', 'maximum', 'oop']):
            return 'out_of_pocket_maximum'
        elif any(term in data_str for term in ['prescription', 'drug', 'pharmacy']):
            return 'prescription_drug'
        elif any(term in data_str for term in ['preventive', 'wellness']):
            return 'preventive_care'
        else:
            return 'other'
    
    def _categorize_benefit(self, benefit_data: Dict[str, str]) -> str:
        """Categorize benefit into broad categories"""
        data_str = ' '.join(benefit_data.values()).lower()
        
        if any(term in data_str for term in ['medical', 'physician', 'doctor', 'hospital']):
            return 'medical'
        elif any(term in data_str for term in ['prescription', 'drug', 'pharmacy']):
            return 'pharmacy'
        elif any(term in data_str for term in ['dental']):
            return 'dental'
        elif any(term in data_str for term in ['vision', 'eye']):
            return 'vision'
        elif any(term in data_str for term in ['mental health', 'behavioral']):
            return 'mental_health'
        else:
            return 'general'
    
    def _generate_benefit_description(self, benefit_data: Dict[str, str]) -> str:
        """Generate human-readable benefit description"""
        # Simple description generation
        items = []
        for key, value in benefit_data.items():
            if value and key and len(key) > 0:
                items.append(f"{key}: {value}")
        
        return "; ".join(items)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        import re
        
        # Health insurance specific keywords
        health_keywords = [
            'deductible', 'copay', 'coinsurance', 'premium', 'network', 'provider',
            'coverage', 'benefit', 'exclusion', 'limitation', 'claim', 'preventive',
            'emergency', 'urgent care', 'specialist', 'primary care', 'prescription',
            'drug', 'pharmacy', 'hospital', 'outpatient', 'inpatient'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in health_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        # Extract dollar amounts and percentages
        amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
        percentages = re.findall(r'\d+%', text)
        
        found_keywords.extend(amounts[:5])  # Limit to 5 amounts
        found_keywords.extend(percentages[:5])  # Limit to 5 percentages
        
        return found_keywords
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate relevance score for chunk"""
        # Simple relevance scoring based on health insurance keywords
        health_terms = [
            'benefit', 'coverage', 'deductible', 'copay', 'coinsurance',
            'network', 'provider', 'claim', 'exclusion', 'limitation'
        ]
        
        text_lower = text.lower()
        found_terms = sum(1 for term in health_terms if term in text_lower)
        
        # Score between 0 and 1
        return min(found_terms / len(health_terms), 1.0)
    
    async def _enhance_chunks_with_ai(self, chunks: List[Dict[str, Any]]):
        """Enhance chunks with AI analysis"""
        if not settings.OPENAI_API_KEY:
            return
        
        try:
            for chunk in chunks:
                if len(chunk['content']) > 100:  # Only process substantial chunks
                    # Analyze chunk with AI
                    analysis = await self._analyze_chunk_with_ai(chunk['content'])
                    
                    # Update chunk with AI insights
                    chunk.update({
                        'entities': analysis.get('entities', []),
                        'topics': analysis.get('topics', []),
                        'confidence_score': analysis.get('confidence_score', 0.5)
                    })
                    
                    # Merge AI keywords with existing ones
                    ai_keywords = analysis.get('keywords', [])
                    chunk['keywords'] = list(set(chunk.get('keywords', []) + ai_keywords))
        
        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
    
    async def _analyze_chunk_with_ai(self, content: str) -> Dict[str, Any]:
        """Analyze chunk content with AI"""
        try:
            prompt = f"""
            Analyze this health insurance document text and extract:
            1. Key entities (amounts, dates, medical terms)
            2. Main topics covered
            3. Important keywords
            4. Confidence score (0-1) for information quality
            
            Text: {content[:1500]}
            
            Respond in JSON format:
            {{
                "entities": ["entity1", "entity2"],
                "topics": ["topic1", "topic2"],
                "keywords": ["keyword1", "keyword2"],
                "confidence_score": 0.8
            }}
            """
            
            response = await openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            import json
            analysis = json.loads(result)
            return analysis
            
        except Exception as e:
            logger.warning(f"AI chunk analysis failed: {e}")
            return {
                'entities': [],
                'topics': [],
                'keywords': [],
                'confidence_score': 0.5
            }
    
    async def _extract_metadata_with_ai(self, text: str) -> Dict[str, Any]:
        """Extract metadata using AI"""
        try:
            prompt = f"""
            Extract metadata from this health insurance document:
            
            Text: {text}
            
            Find and return:
            - Plan name
            - Effective date
            - Plan sponsor/employer
            - Administrator/insurer
            
            Return as JSON:
            {{
                "plan_name": "...",
                "effective_date": "...",
                "plan_sponsor": "...",
                "administrator": "..."
            }}
            """
            
            response = await openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            
            import json
            metadata = json.loads(result)
            return metadata
            
        except Exception as e:
            logger.warning(f"AI metadata extraction failed: {e}")
            return {}


class BPSProcessor:
    """Specialized processor for BPS Excel files with AI enhancement"""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
    
    async def extract_bps_data(self, file_path: str) -> Dict[str, Any]:
        """Extract benefit data from BPS Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
            
            extracted_data = {
                'metadata': {},
                'chunks': [],
                'benefits': [],
                'plan_data': {}
            }
            
            # Process each sheet
            for sheet_name, sheet_df in df.items():
                sheet_data = await self._process_bps_sheet(sheet_df, sheet_name)
                
                # Add sheet data to extracted data
                if sheet_data.get('benefits'):
                    extracted_data['benefits'].extend(sheet_data['benefits'])
                
                if sheet_data.get('plan_data'):
                    extracted_data['plan_data'].update(sheet_data['plan_data'])
                
                # Create summary chunk for this sheet
                if sheet_data.get('summary'):
                    extracted_data['chunks'].append({
                        'content': sheet_data['summary'],
                        'chunk_type': 'benefit_summary',
                        'section_title': f"Sheet: {sheet_name}",
                        'keywords': sheet_data.get('keywords', []),
                        'relevance_score': 0.9,
                        'confidence_score': 0.95
                    })
            
            # Generate overall summary
            overall_summary = await self._generate_bps_summary(extracted_data)
            if overall_summary:
                extracted_data['chunks'].insert(0, {
                    'content': overall_summary,
                    'chunk_type': 'plan_overview',
                    'section_title': 'Plan Overview',
                    'keywords': self._extract_plan_keywords(extracted_data),
                    'relevance_score': 1.0,
                    'confidence_score': 0.95
                })
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"BPS data extraction failed: {e}")
            raise DocumentProcessingError(f"Failed to extract BPS data: {e}")
    
    async def _process_bps_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Process individual BPS sheet"""
        try:
            sheet_data = {
                'benefits': [],
                'plan_data': {},
                'summary': '',
                'keywords': []
            }
            
            # Clean the dataframe
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty:
                return sheet_data
            
            # Detect BPS format type
            format_type = self._detect_bps_format(df)
            
            if format_type == 'tabular':
                sheet_data = await self._process_tabular_bps(df, sheet_name)
            elif format_type == 'pivot':
                sheet_data = await self._process_pivot_bps(df, sheet_name)
            else:
                sheet_data = await self._process_generic_bps(df, sheet_name)
            
            return sheet_data
            
        except Exception as e:
            logger.warning(f"Failed to process BPS sheet {sheet_name}: {e}")
            return {'benefits': [], 'plan_data': {}, 'summary': '', 'keywords': []}
    
    def _detect_bps_format(self, df: pd.DataFrame) -> str:
        """Detect the format type of BPS sheet"""
        # Look for common BPS patterns
        columns = [str(col).lower() for col in df.columns]
        
        # Tabular format indicators
        tabular_indicators = ['benefit', 'in-network', 'out-network', 'copay', 'coinsurance', 'deductible']
        if any(indicator in ' '.join(columns) for indicator in tabular_indicators):
            return 'tabular'
        
        # Pivot format indicators (benefits as rows, network types as columns)
        if len(df.columns) >= 3 and len(df) > 5:
            return 'pivot'
        
        return 'generic'
    
    async def _process_tabular_bps(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Process tabular BPS format"""
        try:
            benefits = []
            plan_data = {}
            
            # Extract benefits row by row
            for index, row in df.iterrows():
                benefit = await self._extract_benefit_from_row(row, index)
                if benefit:
                    benefits.append(benefit)
            
            # Extract plan-level data
            plan_data = self._extract_plan_data_from_df(df)
            
            # Generate summary
            summary = self._generate_sheet_summary(benefits, sheet_name)
            
            # Extract keywords
            keywords = self._extract_sheet_keywords(df)
            
            return {
                'benefits': benefits,
                'plan_data': plan_data,
                'summary': summary,
                'keywords': keywords
            }
            
        except Exception as e:
            logger.warning(f"Failed to process tabular BPS: {e}")
            return {'benefits': [], 'plan_data': {}, 'summary': '', 'keywords': []}
    
    async def _extract_benefit_from_row(self, row: pd.Series, row_index: int) -> Optional[Dict[str, Any]]:
        """Extract benefit information from DataFrame row"""
        try:
            # Convert row to dict and clean
            row_dict = row.dropna().to_dict()
            
            if not row_dict:
                return None
            
            # Find benefit description (usually first text column)
            benefit_description = None
            for key, value in row_dict.items():
                if isinstance(value, str) and len(value) > 5:
                    benefit_description = value
                    break
            
            if not benefit_description:
                return None
            
            # Extract costs and coverage details
            in_network_data = {}
            out_of_network_data = {}
            
            for key, value in row_dict.items():
                key_lower = str(key).lower()
                
                # Categorize by network type
                if 'in-network' in key_lower or 'in network' in key_lower:
                    in_network_data[key] = value
                elif 'out-of-network' in key_lower or 'out of network' in key_lower:
                    out_of_network_data[key] = value
            
            # Create benefit object
            benefit = {
                'id': str(uuid.uuid4()),
                'benefit_type': self._classify_benefit_type_from_description(benefit_description),
                'category': self._categorize_benefit_from_description(benefit_description),
                'description': benefit_description,
                'in_network_coverage': in_network_data,
                'out_of_network_coverage': out_of_network_data,
                'raw_data': row_dict,
                'row_index': row_index,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Extract specific values
            benefit.update(self._extract_specific_benefit_values(row_dict))
            
            return benefit
            
        except Exception as e:
            logger.warning(f"Failed to extract benefit from row {row_index}: {e}")
            return None
    
    def _classify_benefit_type_from_description(self, description: str) -> str:
        """Classify benefit type from description"""
        desc_lower = description.lower()
        
        if any(term in desc_lower for term in ['primary care', 'pcp', 'family doctor']):
            return 'primary_care'
        elif any(term in desc_lower for term in ['specialist', 'specialty']):
            return 'specialist'
        elif any(term in desc_lower for term in ['emergency', 'er', 'emergency room']):
            return 'emergency_room'
        elif any(term in desc_lower for term in ['urgent care']):
            return 'urgent_care'
        elif any(term in desc_lower for term in ['hospital', 'inpatient']):
            return 'inpatient'
        elif any(term in desc_lower for term in ['outpatient', 'surgery']):
            return 'outpatient'
        elif any(term in desc_lower for term in ['prescription', 'drug', 'pharmacy']):
            return 'prescription_drug'
        elif any(term in desc_lower for term in ['preventive', 'wellness', 'physical']):
            return 'preventive_care'
        elif any(term in desc_lower for term in ['mental health', 'behavioral']):
            return 'mental_health'
        elif any(term in desc_lower for term in ['deductible']):
            return 'deductible'
        else:
            return 'other'
    
    def _categorize_benefit_from_description(self, description: str) -> str:
        """Categorize benefit from description"""
        desc_lower = description.lower()
        
        if any(term in desc_lower for term in ['prescription', 'drug', 'pharmacy']):
            return 'pharmacy'
        elif any(term in desc_lower for term in ['dental']):
            return 'dental'
        elif any(term in desc_lower for term in ['vision', 'eye']):
            return 'vision'
        elif any(term in desc_lower for term in ['mental health', 'behavioral']):
            return 'mental_health'
        else:
            return 'medical'
    
    def _extract_specific_benefit_values(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific benefit values like copays, deductibles, etc."""
        import re
        
        values = {}
        
        for key, value in row_dict.items():
            if pd.isna(value):
                continue
            
            value_str = str(value)
            key_lower = str(key).lower()
            
            # Extract dollar amounts
            dollar_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', value_str)
            if dollar_match:
                amount = float(dollar_match.group(1).replace(',', ''))
                
                if 'copay' in key_lower:
                    values['copay'] = amount
                elif 'deductible' in key_lower:
                    values['deductible_applies'] = True
                elif 'coinsurance' in key_lower:
                    # Extract percentage if present
                    pct_match = re.search(r'(\d+)%', value_str)
                    if pct_match:
                        values['coinsurance'] = float(pct_match.group(1)) / 100
            
            # Extract percentages
            pct_match = re.search(r'(\d+)%', value_str)
            if pct_match and 'coinsurance' in key_lower:
                values['coinsurance'] = float(pct_match.group(1)) / 100
            
            # Check for prior authorization requirements
            if any(term in value_str.lower() for term in ['prior auth', 'authorization', 'referral']):
                values['prior_auth_required'] = True
        
        return values
    
    def _extract_plan_data_from_df(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract plan-level data from DataFrame"""
        plan_data = {}
        
        try:
            # Look for plan-level information in the DataFrame
            for index, row in df.iterrows():
                for col, value in row.items():
                    if pd.isna(value):
                        continue
                    
                    col_str = str(col).lower()
                    value_str = str(value).lower()
                    
                    # Extract deductibles
                    if 'deductible' in col_str or 'deductible' in value_str:
                        if 'individual' in col_str or 'individual' in value_str:
                            amount = self._extract_amount(str(value))
                            if amount:
                                plan_data['deductible_individual'] = amount
                        elif 'family' in col_str or 'family' in value_str:
                            amount = self._extract_amount(str(value))
                            if amount:
                                plan_data['deductible_family'] = amount
                    
                    # Extract out-of-pocket maximums
                    if 'out-of-pocket' in col_str or 'maximum' in col_str:
                        if 'individual' in col_str:
                            amount = self._extract_amount(str(value))
                            if amount:
                                plan_data['out_of_pocket_max_individual'] = amount
                        elif 'family' in col_str:
                            amount = self._extract_amount(str(value))
                            if amount:
                                plan_data['out_of_pocket_max_family'] = amount
        
        except Exception as e:
            logger.warning(f"Failed to extract plan data: {e}")
        
        return plan_data
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract dollar amount from text"""
        import re
        
        # Look for dollar amounts
        match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if match:
            return float(match.group(1).replace(',', ''))
        
        # Look for numeric amounts
        match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if match:
            return float(match.group(1).replace(',', ''))
        
        return None
    
    async def _process_pivot_bps(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Process pivot-style BPS format"""
        # Similar to tabular but with different structure
        return await self._process_tabular_bps(df, sheet_name)
    
    async def _process_generic_bps(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Process generic BPS format"""
        # Fallback processing for unknown formats
        return await self._process_tabular_bps(df, sheet_name)
    
    def _generate_sheet_summary(self, benefits: List[Dict[str, Any]], sheet_name: str) -> str:
        """Generate summary for BPS sheet"""
        if not benefits:
            return f"Sheet {sheet_name} contains no extractable benefit information."
        
        summary_parts = [f"Sheet {sheet_name} contains {len(benefits)} benefits:"]
        
        # Group benefits by category
        categories = {}
        for benefit in benefits:
            category = benefit.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(benefit)
        
        # Summarize each category
        for category, cat_benefits in categories.items():
            benefit_types = [b.get('benefit_type', 'unknown') for b in cat_benefits]
            unique_types = list(set(benefit_types))
            summary_parts.append(f"- {category.title()}: {', '.join(unique_types)}")
        
        return '\n'.join(summary_parts)
    
    def _extract_sheet_keywords(self, df: pd.DataFrame) -> List[str]:
        """Extract keywords from BPS sheet"""
        keywords = set()
        
        # Extract from column names
        for col in df.columns:
            col_str = str(col).lower()
            if any(term in col_str for term in ['copay', 'deductible', 'coinsurance', 'network']):
                keywords.add(col_str)
        
        # Extract from cell values (sample)
        sample_cells = df.head(10).values.flatten()
        for cell in sample_cells:
            if pd.notna(cell):
                cell_str = str(cell).lower()
                health_terms = ['copay', 'deductible', 'coinsurance', 'prior auth', 'network']
                for term in health_terms:
                    if term in cell_str:
                        keywords.add(term)
        
        return list(keywords)
    
    async def _generate_bps_summary(self, extracted_data: Dict[str, Any]) -> str:
        """Generate overall BPS summary"""
        try:
            total_benefits = len(extracted_data.get('benefits', []))
            plan_data = extracted_data.get('plan_data', {})
            
            summary_parts = [
                f"This BPS file contains {total_benefits} benefits across multiple categories."
            ]
            
            # Add plan-level information
            if plan_data.get('deductible_individual'):
                summary_parts.append(f"Individual deductible: ${plan_data['deductible_individual']:,.2f}")
            
            if plan_data.get('deductible_family'):
                summary_parts.append(f"Family deductible: ${plan_data['deductible_family']:,.2f}")
            
            if plan_data.get('out_of_pocket_max_individual'):
                summary_parts.append(f"Individual out-of-pocket maximum: ${plan_data['out_of_pocket_max_individual']:,.2f}")
            
            if plan_data.get('out_of_pocket_max_family'):
                summary_parts.append(f"Family out-of-pocket maximum: ${plan_data['out_of_pocket_max_family']:,.2f}")
            
            # Categorize benefits
            benefits = extracted_data.get('benefits', [])
            categories = {}
            for benefit in benefits:
                category = benefit.get('category', 'other')
                categories[category] = categories.get(category, 0) + 1
            
            if categories:
                summary_parts.append("Benefit categories:")
                for category, count in categories.items():
                    summary_parts.append(f"- {category.title()}: {count} benefits")
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Failed to generate BPS summary: {e}")
            return "BPS file processed successfully."
    
    def _extract_plan_keywords(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Extract plan-level keywords"""
        keywords = set()
        
        # Add standard plan keywords
        keywords.update(['health plan', 'benefits', 'coverage', 'bps'])
        
        # Add from plan data
        plan_data = extracted_data.get('plan_data', {})
        if plan_data:
            keywords.update(['deductible', 'out-of-pocket', 'maximum'])
        
        # Add from benefits
        benefits = extracted_data.get('benefits', [])
        for benefit in benefits[:10]:  # Sample first 10
            benefit_keywords = benefit.get('keywords', [])
            keywords.update(benefit_keywords[:3])  # Add top 3 keywords per benefit
        
        return list(keywords)