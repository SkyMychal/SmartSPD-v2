"""
Advanced RAG (Retrieval-Augmented Generation) service for health plan queries
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.services.ai_service import ai_service
from app.services.vector_service import VectorService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.crud.document import document_chunk_crud
from sqlalchemy.orm import Session
from app.core.database import get_db

logger = logging.getLogger(__name__)

class RAGService:
    """Advanced RAG service for health plan question answering"""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.kg_service = KnowledgeGraphService()
        self.ai_service = ai_service
        
        # Expert system prompt
        self.expert_prompt = """
        You are a highly experienced health insurance expert with over 30 years of experience in TPA operations and customer service. You understand complex health plan benefits, coverage details, and member needs deeply.

        Your role is to provide accurate, professional, and helpful responses to health plan questions based on the provided documents and context. You should:

        1. Always reference specific document sources when providing information
        2. Use professional but approachable language suitable for customer service agents
        3. Provide clear, actionable answers that agents can communicate to members
        4. Include relevant costs, coverage details, and any limitations or exclusions
        5. Mention if prior authorization or referrals are required
        6. Distinguish between in-network and out-of-network coverage when relevant
        7. If information is unclear or missing, explicitly state this rather than guessing

        Response format:
        - Start with a direct answer to the question
        - Provide specific details (costs, coverage percentages, etc.)
        - Include any important limitations or exclusions
        - End with source references and confidence level

        Remember: Accuracy is paramount. It's better to say "I don't have enough information" than to provide incorrect details.
        """
    
    async def process_query(
        self,
        db: Session,
        query: str,
        tpa_id: str,
        health_plan_id: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a health plan query and return intelligent response"""
        
        try:
            # Analyze query intent and complexity
            query_analysis = await self._analyze_query(query)
            
            # Retrieve relevant information
            retrieval_results = await self._retrieve_information(
                db, query, tpa_id, health_plan_id, query_analysis
            )
            
            # Generate AI response
            response = await self._generate_response(
                query, retrieval_results, query_analysis, conversation_context
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                response, retrieval_results, query_analysis
            )
            
            return {
                'answer': response['answer'],
                'reasoning': response.get('reasoning', ''),
                'confidence_score': confidence_score,
                'query_intent': query_analysis['intent'],
                'query_complexity': query_analysis['complexity'],
                'source_documents': retrieval_results['sources'],
                'related_topics': response.get('related_topics', []),
                'follow_up_suggestions': response.get('follow_up_suggestions', []),
                'processing_time': retrieval_results['processing_time'],
                'token_count': response.get('token_count', 0)
            }
            
        except Exception as e:
            logger.error(f"RAG query processing failed: {e}")
            raise AIServiceError(f"Failed to process query: {e}", "RAG")
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Enhanced query analysis with healthcare-specific entity recognition"""
        
        try:
            # Enhanced prompt with healthcare-specific guidance
            analysis_prompt = f"""
            You are an expert healthcare benefits analyst. Analyze this health insurance query and extract detailed information:
            
            Query: "{query}"
            
            Extract the following information in JSON format:
            {{
                "intent": "coverage|cost|network|authorization|claims|general",
                "complexity": "simple|medium|complex",
                "entities": ["entity1", "entity2"],
                "benefit_types": ["primary_care", "specialist", "emergency", "prescription", "preventive", "mental_health", "hospital", "urgent_care"],
                "keywords": ["keyword1", "keyword2"],
                "requires_calculation": boolean,
                "member_specific": boolean,
                "document_types_needed": ["spd", "bps", "both"],
                "query_type": "benefit_lookup|cost_calculation|coverage_verification|comparison|procedure_coverage",
                "healthcare_entities": {{
                    "medical_procedures": [],
                    "medications": [],
                    "providers": [],
                    "body_parts": [],
                    "conditions": [],
                    "amounts": []
                }},
                "cross_reference_needed": boolean,
                "confidence_level": "high|medium|low"
            }}
            
            Be thorough in extracting healthcare-specific entities and determining if cross-referencing between SPD and BPS documents is needed.
            """
            
            ai_response = await self.ai_service.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.1
            )
            
            analysis = json.loads(ai_response.content)
            
            # Add additional pattern-based analysis
            analysis.update(self._pattern_based_analysis(query))
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Enhanced query analysis failed, using fallback: {e}")
            return self._fallback_analysis(query)
    
    def _pattern_based_analysis(self, query: str) -> Dict[str, Any]:
        """Pattern-based query analysis as fallback"""
        
        query_lower = query.lower()
        
        # Intent patterns
        intent = "general"
        if any(word in query_lower for word in ['cost', 'pay', 'copay', 'deductible', 'price', '$']):
            intent = "cost"
        elif any(word in query_lower for word in ['cover', 'covered', 'coverage', 'benefit']):
            intent = "coverage"
        elif any(word in query_lower for word in ['network', 'provider', 'doctor', 'hospital']):
            intent = "network"
        elif any(word in query_lower for word in ['authorization', 'referral', 'approval']):
            intent = "authorization"
        elif any(word in query_lower for word in ['claim', 'billing', 'reimburse']):
            intent = "claims"
        
        # Complexity assessment
        complexity = "simple"
        if len(query.split()) > 15 or query.count('?') > 1:
            complexity = "medium"
        if any(word in query_lower for word in ['compare', 'difference', 'better', 'vs', 'versus']):
            complexity = "complex"
        
        # Extract benefit types
        benefit_types = []
        benefit_patterns = {
            'primary_care': ['primary care', 'pcp', 'family doctor'],
            'specialist': ['specialist', 'specialty'],
            'emergency': ['emergency', 'er', 'emergency room'],
            'urgent_care': ['urgent care'],
            'prescription': ['prescription', 'drug', 'medication', 'pharmacy'],
            'hospital': ['hospital', 'inpatient'],
            'preventive': ['preventive', 'wellness', 'physical', 'checkup']
        }
        
        for benefit_type, patterns in benefit_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                benefit_types.append(benefit_type)
        
        return {
            'intent': intent,
            'complexity': complexity,
            'benefit_types': benefit_types,
            'member_specific': any(word in query_lower for word in ['my', 'i', 'me'])
        }
    
    def _fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback analysis when AI analysis fails"""
        pattern_analysis = self._pattern_based_analysis(query)
        
        return {
            'intent': pattern_analysis.get('intent', 'general'),
            'complexity': pattern_analysis.get('complexity', 'simple'),
            'entities': [],
            'benefit_types': pattern_analysis.get('benefit_types', []),
            'keywords': query.lower().split()[:10],  # First 10 words as keywords
            'requires_calculation': '$' in query or any(word in query.lower() for word in ['cost', 'pay', 'amount']),
            'member_specific': pattern_analysis.get('member_specific', False)
        }
    
    async def _retrieve_information(
        self,
        db: Session,
        query: str,
        tpa_id: str,
        health_plan_id: Optional[str],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced retrieval with multi-hop traversal and cross-referencing"""
        
        start_time = datetime.utcnow()
        
        # 1. Adaptive vector search based on query complexity
        vector_results = []
        if self.vector_service.initialized:
            try:
                # Adjust search parameters based on query analysis
                top_k = 15 if query_analysis.get('complexity') == 'complex' else 10
                score_threshold = 0.6 if query_analysis.get('complexity') == 'complex' else 0.7
                
                vector_results = await self.vector_service.search_similar_chunks(
                    query=query,
                    tpa_id=tpa_id,
                    health_plan_id=health_plan_id,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # 2. Enhanced knowledge graph search with multi-hop traversal
        kg_results = []
        if self.kg_service.initialized and health_plan_id:
            try:
                benefit_types = query_analysis.get('benefit_types', [])
                if benefit_types:
                    # Multi-hop traversal for complex queries
                    max_hops = 3 if query_analysis.get('complexity') == 'complex' else 1
                    kg_results = await self.kg_service.find_related_benefits_multi_hop(
                        health_plan_id, benefit_types, max_hops
                    )
            except Exception as e:
                logger.warning(f"Knowledge graph search failed: {e}")
        
        # 3. SPD/BPS cross-referencing if needed
        cross_ref_results = []
        if query_analysis.get('cross_reference_needed') and health_plan_id:
            try:
                cross_ref_results = await self._cross_reference_spd_bps(
                    db, tpa_id, health_plan_id, query_analysis
                )
            except Exception as e:
                logger.warning(f"Cross-reference search failed: {e}")
        
        # 4. Traditional database search as fallback
        db_results = []
        try:
            db_results = await document_chunk_crud.search_chunks(
                db=db,
                tpa_id=tpa_id,
                query=query,
                health_plan_id=health_plan_id,
                limit=15
            )
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
        
        # Combine and rank results with confidence scoring
        combined_results = self._combine_search_results_with_confidence(
            vector_results, kg_results, db_results, cross_ref_results, query_analysis
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'chunks': combined_results,
            'sources': self._extract_sources(combined_results),
            'processing_time': processing_time,
            'vector_count': len(vector_results),
            'kg_count': len(kg_results),
            'db_count': len(db_results),
            'cross_ref_count': len(cross_ref_results)
        }
    
    def _combine_search_results_with_confidence(
        self,
        vector_results: List[Dict[str, Any]],
        kg_results: List[Dict[str, Any]],
        db_results: List[Any],
        cross_ref_results: List[Dict[str, Any]],
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Combine and rank search results with confidence scoring"""
        
        combined = []
        
        # Add vector results with confidence-based scoring
        for result in vector_results:
            confidence = self._calculate_result_confidence(result, 'vector', query_analysis)
            combined.append({
                'content': result['text'],
                'source': 'vector',
                'score': result['score'],
                'confidence': confidence,
                'document_id': result.get('document_id'),
                'chunk_type': result.get('chunk_type'),
                'page_number': result.get('page_number'),
                'section_title': result.get('section_title')
            })
        
        # Add knowledge graph results with high confidence
        for result in kg_results:
            confidence = 0.9  # High confidence for structured data
            combined.append({
                'content': result.get('description', ''),
                'source': 'knowledge_graph',
                'score': 0.9,
                'confidence': confidence,
                'benefit_type': result.get('benefit_type'),
                'category': result.get('category'),
                'benefit_data': result
            })
        
        # Add cross-reference results with very high confidence
        for result in cross_ref_results:
            confidence = 0.95  # Very high confidence for cross-referenced data
            combined.append({
                'content': result['content'],
                'source': 'cross_reference',
                'score': 0.95,
                'confidence': confidence,
                'spd_reference': result.get('spd_reference'),
                'bps_reference': result.get('bps_reference'),
                'cross_ref_type': result.get('cross_ref_type')
            })
        
        # Add database results
        for chunk in db_results:
            confidence = self._calculate_result_confidence(chunk, 'database', query_analysis)
            combined.append({
                'content': chunk.content,
                'source': 'database',
                'score': chunk.relevance_score or 0.5,
                'confidence': confidence,
                'document_id': chunk.document_id,
                'chunk_type': chunk.chunk_type,
                'page_number': chunk.page_number,
                'section_title': chunk.section_title,
                'keywords': chunk.keywords
            })
        
        # Remove duplicates and sort by confidence and score
        seen_content = set()
        unique_results = []
        
        for result in sorted(combined, key=lambda x: (x['confidence'], x['score']), reverse=True):
            content_hash = hash(result['content'][:100])  # First 100 chars
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        # Return top results
        return unique_results[:10]
    
    async def _cross_reference_spd_bps(
        self,
        db: Session,
        tpa_id: str,
        health_plan_id: str,
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Cross-reference SPD and BPS documents for comprehensive answers"""
        
        cross_ref_results = []
        
        try:
            # Get SPD chunks that mention benefit types
            spd_chunks = await document_chunk_crud.search_chunks(
                db=db,
                tpa_id=tpa_id,
                query=" ".join(query_analysis.get('benefit_types', [])),
                health_plan_id=health_plan_id,
                document_type='spd',
                limit=10
            )
            
            # Get BPS chunks with corresponding amounts
            bps_chunks = await document_chunk_crud.search_chunks(
                db=db,
                tpa_id=tpa_id,
                query=" ".join(query_analysis.get('benefit_types', [])),
                health_plan_id=health_plan_id,
                document_type='bps',
                limit=10
            )
            
            # Use AI to find connections between SPD and BPS
            if spd_chunks and bps_chunks:
                connection_prompt = f"""
                Find connections between these SPD (Summary Plan Description) and BPS (Benefit Payment Schedule) sections:
                
                SPD Sections:
                {chr(10).join([f"SPD-{i+1}: {chunk.content[:300]}" for i, chunk in enumerate(spd_chunks[:3])])}
                
                BPS Sections:
                {chr(10).join([f"BPS-{i+1}: {chunk.content[:300]}" for i, chunk in enumerate(bps_chunks[:3])])}
                
                Query: {query_analysis.get('keywords', [])}
                
                Identify which SPD rules correspond to which BPS amounts. Return as JSON:
                {{
                    "connections": [
                        {{
                            "spd_section": "SPD-1",
                            "bps_section": "BPS-1",
                            "connection_type": "coverage_amount|copay|deductible|coinsurance",
                            "combined_content": "Combined explanation...",
                            "confidence": 0.85
                        }}
                    ]
                }}
                """
                
                ai_response = await self.ai_service.chat_completion(
                    messages=[{"role": "user", "content": connection_prompt}],
                    model="gpt-4o-mini",
                    max_tokens=800,
                    temperature=0.1
                )
                
                connections = json.loads(ai_response.content)
                
                for conn in connections.get('connections', []):
                    cross_ref_results.append({
                        'content': conn['combined_content'],
                        'spd_reference': conn['spd_section'],
                        'bps_reference': conn['bps_section'],
                        'cross_ref_type': conn['connection_type'],
                        'confidence': conn['confidence']
                    })
        
        except Exception as e:
            logger.warning(f"SPD/BPS cross-referencing failed: {e}")
        
        return cross_ref_results
    
    def _calculate_result_confidence(
        self,
        result: Any,
        source_type: str,
        query_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for individual search results"""
        
        base_confidence = 0.5
        
        # Source-specific confidence
        if source_type == 'vector':
            base_confidence = 0.7
        elif source_type == 'knowledge_graph':
            base_confidence = 0.9
        elif source_type == 'cross_reference':
            base_confidence = 0.95
        elif source_type == 'database':
            base_confidence = 0.6
        
        # Adjust based on query complexity match
        if query_analysis.get('complexity') == 'simple':
            base_confidence += 0.1
        elif query_analysis.get('complexity') == 'complex':
            base_confidence -= 0.1
        
        # Adjust based on benefit type match
        if hasattr(result, 'chunk_type') and result.chunk_type in query_analysis.get('benefit_types', []):
            base_confidence += 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from results"""
        
        sources = []
        
        for result in results:
            source = {
                'type': result['source'],
                'score': result['score']
            }
            
            if result.get('document_id'):
                source['document_id'] = result['document_id']
            
            if result.get('page_number'):
                source['page_number'] = result['page_number']
            
            if result.get('section_title'):
                source['section_title'] = result['section_title']
            
            if result.get('chunk_type'):
                source['chunk_type'] = result['chunk_type']
            
            sources.append(source)
        
        return sources
    
    async def _generate_response(
        self,
        query: str,
        retrieval_results: Dict[str, Any],
        query_analysis: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI response using retrieved information"""
        
        try:
            # Prepare context from retrieved chunks
            context_chunks = []
            for i, chunk in enumerate(retrieval_results['chunks'][:5]):  # Top 5 chunks
                context_chunks.append(f"Source {i+1}: {chunk['content'][:800]}...")
            
            context = "\n\n".join(context_chunks)
            
            # Build conversation context
            conv_context = ""
            if conversation_context and conversation_context.get('previous_queries'):
                conv_context = f"\nPrevious conversation context:\n{conversation_context['previous_queries']}\n"
            
            # Enhanced response generation with multi-step reasoning
            response_prompt = f"""
            {self.expert_prompt}
            
            Query: "{query}"
            Query Intent: {query_analysis['intent']}
            Query Complexity: {query_analysis['complexity']}
            Query Type: {query_analysis.get('query_type', 'general')}
            Healthcare Entities: {query_analysis.get('healthcare_entities', {})}
            Cross-Reference Needed: {query_analysis.get('cross_reference_needed', False)}
            {conv_context}
            
            Available Information:
            {context}
            
            Please provide a comprehensive, accurate response using multi-step reasoning:
            
            Step 1: Analyze the query and identify the specific healthcare benefit being asked about
            Step 2: Review the available information and identify the most relevant sources
            Step 3: If cross-referencing is needed, connect SPD rules with BPS amounts
            Step 4: Synthesize a complete answer with specific details
            Step 5: Verify the answer against the source material
            
            Include in your response:
            1. Direct answer to the question with specific details
            2. Exact costs, percentages, or coverage amounts when available
            3. Any limitations, exclusions, or requirements (deductibles, prior auth, etc.)
            4. Network considerations (in-network vs out-of-network)
            5. Source references with specific page numbers when available
            6. Confidence level based on information quality
            
            Also suggest 2-3 related follow-up questions that members commonly ask.
            
            Format your response as JSON:
            {{
                "answer": "Your detailed response with specific amounts and requirements...",
                "reasoning": "Step-by-step explanation of how you arrived at this answer",
                "confidence_level": "High/Medium/Low",
                "related_topics": ["topic1", "topic2"],
                "follow_up_suggestions": ["question1?", "question2?", "question3?"],
                "requires_clarification": boolean,
                "cross_referenced_data": {{
                    "spd_rules": "Relevant SPD rules if applicable",
                    "bps_amounts": "Corresponding BPS amounts if applicable"
                }}
            }}
            """
            
            ai_response = await self.ai_service.chat_completion(
                messages=[{"role": "user", "content": response_prompt}],
                model="gpt-4",
                max_tokens=1500,
                temperature=0.1
            )
            
            response_content = ai_response.content
            token_count = ai_response.token_count
            
            # Parse JSON response
            parsed_response = json.loads(response_content)
            parsed_response['token_count'] = token_count
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            
            # Fallback response
            return {
                'answer': self._generate_fallback_response(query, retrieval_results),
                'reasoning': 'Generated using fallback method due to AI service unavailability',
                'confidence_level': 'Low',
                'related_topics': [],
                'follow_up_suggestions': [],
                'requires_clarification': True,
                'token_count': 0
            }
    
    def _generate_fallback_response(
        self, 
        query: str, 
        retrieval_results: Dict[str, Any]
    ) -> str:
        """Generate fallback response when AI is unavailable"""
        
        if not retrieval_results['chunks']:
            return "I don't have enough information to answer your question. Please provide more details or contact your plan administrator."
        
        # Use the most relevant chunk
        best_chunk = retrieval_results['chunks'][0]
        
        return f"""Based on the available plan documents, here's the relevant information:

{best_chunk['content'][:500]}...

Please note: This is a direct excerpt from your plan documents. For specific questions about your coverage, I recommend speaking with a customer service representative who can provide personalized assistance.

Source: Plan documentation"""
    
    def _calculate_confidence_score(
        self,
        response: Dict[str, Any],
        retrieval_results: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the response"""
        
        confidence = 0.5  # Base confidence
        
        # Adjust based on retrieval quality
        if retrieval_results['chunks']:
            avg_score = sum(chunk['score'] for chunk in retrieval_results['chunks']) / len(retrieval_results['chunks'])
            confidence += (avg_score - 0.5) * 0.3  # +/- 0.3 based on retrieval scores
        
        # Adjust based on AI confidence level
        ai_confidence = response.get('confidence_level', 'Medium')
        if ai_confidence == 'High':
            confidence += 0.2
        elif ai_confidence == 'Low':
            confidence -= 0.2
        
        # Adjust based on query complexity
        complexity = query_analysis.get('complexity', 'simple')
        if complexity == 'simple':
            confidence += 0.1
        elif complexity == 'complex':
            confidence -= 0.1
        
        # Adjust based on number of sources
        source_count = len(retrieval_results.get('sources', []))
        if source_count >= 3:
            confidence += 0.1
        elif source_count == 0:
            confidence -= 0.3
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    async def get_query_suggestions(
        self,
        db: Session,
        tpa_id: str,
        health_plan_id: Optional[str] = None,
        limit: int = 10
    ) -> List[str]:
        """Get common query suggestions"""
        
        suggestions = [
            "What is my deductible?",
            "How much is a primary care visit?",
            "What's covered for preventive care?",
            "Do I need a referral for specialists?",
            "What's my out-of-pocket maximum?",
            "Is emergency room care covered?",
            "What prescription drugs are covered?",
            "How does out-of-network coverage work?",
            "What mental health services are covered?",
            "Do I need prior authorization for surgery?"
        ]
        
        # TODO: Generate personalized suggestions based on:
        # - Most common queries for this TPA
        # - Plan-specific benefits
        # - Seasonal trends
        
        return suggestions[:limit]