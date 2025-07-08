"""
Vector database service using Pinecone
"""
import pinecone
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations using Pinecone"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Pinecone connection"""
        try:
            # Initialize Pinecone
            self.pc = pinecone.Pinecone(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )
            
            # Connect to index
            index_name = settings.PINECONE_INDEX_NAME
            
            # Check if index exists, create if not
            existing_indexes = self.pc.list_indexes()
            if index_name not in [idx.name for idx in existing_indexes]:
                logger.info(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            
            self.index = self.pc.Index(index_name)
            self.initialized = True
            
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise AIServiceError(f"Vector service initialization failed: {e}", "Pinecone")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using AI service"""
        try:
            return await ai_service.create_embedding(text.replace("\n", " "))
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise AIServiceError(f"Embedding generation failed: {e}", "AI_SERVICE")
    
    async def upsert_document_chunk(
        self,
        chunk_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Store document chunk in vector database"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)
            
            # Prepare metadata (Pinecone has metadata size limits)
            pinecone_metadata = {
                "text": text[:8000],  # Limit text size
                "tpa_id": metadata.get("tpa_id"),
                "document_id": metadata.get("document_id"),
                "document_type": metadata.get("document_type"),
                "health_plan_id": metadata.get("health_plan_id"),
                "chunk_index": metadata.get("chunk_index"),
                "page_number": metadata.get("page_number"),
                "section_title": metadata.get("section_title", "")[:100],
                "chunk_type": metadata.get("chunk_type"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Remove None values
            pinecone_metadata = {k: v for k, v in pinecone_metadata.items() if v is not None}
            
            # Upsert to Pinecone
            self.index.upsert([(chunk_id, embedding, pinecone_metadata)])
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert document chunk: {e}")
            raise AIServiceError(f"Vector upsert failed: {e}", "Pinecone")
    
    async def search_similar_chunks(
        self,
        query: str,
        tpa_id: str,
        health_plan_id: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar document chunks"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Build filter
            filter_dict = {"tpa_id": {"$eq": tpa_id}}
            
            if health_plan_id:
                filter_dict["health_plan_id"] = {"$eq": health_plan_id}
            
            if document_type:
                filter_dict["document_type"] = {"$eq": document_type}
            
            # Search Pinecone
            search_response = self.index.query(
                vector=query_embedding,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Process results
            results = []
            for match in search_response.matches:
                if match.score >= score_threshold:
                    result = {
                        "chunk_id": match.id,
                        "score": float(match.score),
                        "text": match.metadata.get("text", ""),
                        "document_id": match.metadata.get("document_id"),
                        "document_type": match.metadata.get("document_type"),
                        "health_plan_id": match.metadata.get("health_plan_id"),
                        "chunk_index": match.metadata.get("chunk_index"),
                        "page_number": match.metadata.get("page_number"),
                        "section_title": match.metadata.get("section_title"),
                        "chunk_type": match.metadata.get("chunk_type")
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            raise AIServiceError(f"Vector search failed: {e}", "Pinecone")
    
    async def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a document"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Delete by filter
            self.index.delete(filter={"document_id": {"$eq": document_id}})
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {e}")
            raise AIServiceError(f"Vector deletion failed: {e}", "Pinecone")
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.initialized:
            await self.initialize()
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}