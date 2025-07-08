"""
Enhanced document processor methods for SPD and BPS specialization
"""
import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class DocumentProcessorEnhanced:
    """Enhanced methods for document processing with AI specialization"""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
    
    async def extract_spd_content_enhanced(self, file_path: str, tpa_id: str) -> Dict[str, Any]:
        """Enhanced SPD extraction with document type specialization"""
        try:
            # First do standard extraction
            extracted_data = await self.extract_spd_content(file_path)
            
            # Then enhance with AI-powered document understanding
            if self.ai_service:
                enhanced_data = await self._enhance_document_understanding(extracted_data, 'spd', tpa_id)
                extracted_data.update(enhanced_data)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Enhanced SPD extraction failed: {e}")
            # Fallback to standard extraction
            return await self.extract_spd_content(file_path)
    
    async def _enhance_document_understanding(self, extracted_data: Dict[str, Any], doc_type: str, tpa_id: str) -> Dict[str, Any]:
        """Enhance document understanding with AI analysis"""
        try:
            # Analyze document structure and content
            chunks = extracted_data.get('chunks', [])
            if not chunks:
                return {}
            
            # Sample content for analysis
            sample_content = '\n'.join([chunk['content'][:500] for chunk in chunks[:5]])
            
            analysis_prompt = f"""
            Analyze this {doc_type.upper()} document content and enhance understanding:
            
            Content Sample:
            {sample_content}
            
            Provide enhanced analysis in JSON format:
            {{
                "document_structure": {{
                    "sections_identified": ["section1", "section2"],
                    "benefit_categories": ["medical", "pharmacy"],
                    "coverage_types": ["in_network", "out_of_network"]
                }},
                "key_entities": {{
                    "benefit_types": ["primary_care", "specialist"],
                    "amounts": ["$20", "$50"],
                    "percentages": ["80%", "60%"],
                    "medical_terms": ["deductible", "copay"]
                }},
                "document_confidence": 0.9,
                "processing_recommendations": ["focus_on_tables", "extract_amounts"]
            }}
            """
            
            ai_response = await self.ai_service.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                model="gpt-4o-mini",
                max_tokens=600,
                temperature=0.1
            )
            
            enhancement = json.loads(ai_response.content)
            
            return {
                'enhanced_structure': enhancement.get('document_structure', {}),
                'enhanced_entities': enhancement.get('key_entities', {}),
                'document_confidence': enhancement.get('document_confidence', 0.5),
                'processing_recommendations': enhancement.get('processing_recommendations', [])
            }
            
        except Exception as e:
            logger.warning(f"Document understanding enhancement failed: {e}")
            return {}
    
    async def _enhance_chunks_with_ai_advanced(self, chunks: List[Dict[str, Any]]):
        """Advanced AI enhancement of chunks with healthcare specialization"""
        if not self.ai_service:
            return
        
        try:
            for chunk in chunks:
                if len(chunk['content']) > 100:  # Only process substantial chunks
                    # Advanced analysis with healthcare focus
                    analysis = await self._analyze_chunk_with_ai_advanced(chunk['content'])
                    
                    # Update chunk with enhanced AI insights
                    chunk.update({
                        'entities': analysis.get('entities', []),
                        'topics': analysis.get('topics', []),
                        'confidence_score': analysis.get('confidence_score', 0.5),
                        'healthcare_entities': analysis.get('healthcare_entities', {}),
                        'benefit_relationships': analysis.get('benefit_relationships', []),
                        'cross_reference_potential': analysis.get('cross_reference_potential', False)
                    })
                    
                    # Merge AI keywords with existing ones
                    ai_keywords = analysis.get('keywords', [])
                    chunk['keywords'] = list(set(chunk.get('keywords', []) + ai_keywords))
        
        except Exception as e:
            logger.warning(f"Advanced AI enhancement failed: {e}")
    
    async def _analyze_chunk_with_ai_advanced(self, content: str) -> Dict[str, Any]:
        """Advanced AI analysis with healthcare specialization"""
        try:
            prompt = f"""
            Analyze this health insurance SPD document text with advanced healthcare expertise:
            
            Text: {content[:1500]}
            
            Extract and analyze:
            1. Healthcare-specific entities (procedures, conditions, providers)
            2. Benefit relationships and dependencies
            3. Cross-reference potential with BPS documents
            4. Coverage rules and limitations
            5. Network restrictions and requirements
            
            Respond in JSON format:
            {{
                "entities": ["entity1", "entity2"],
                "topics": ["topic1", "topic2"],
                "keywords": ["keyword1", "keyword2"],
                "confidence_score": 0.8,
                "healthcare_entities": {{
                    "procedures": [],
                    "conditions": [],
                    "providers": [],
                    "medications": []
                }},
                "benefit_relationships": [
                    {{
                        "source_benefit": "primary_care",
                        "related_benefit": "referral_requirement",
                        "relationship_type": "prerequisite"
                    }}
                ],
                "cross_reference_potential": true,
                "coverage_rules": [],
                "network_requirements": []
            }}
            """
            
            ai_response = await self.ai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=700,
                temperature=0.1
            )
            
            analysis = json.loads(ai_response.content)
            return analysis
            
        except Exception as e:
            logger.warning(f"Advanced AI chunk analysis failed: {e}")
            return {
                'entities': [],
                'topics': [],
                'keywords': [],
                'confidence_score': 0.5,
                'healthcare_entities': {},
                'benefit_relationships': [],
                'cross_reference_potential': False
            }
    
    async def extract_bps_data_enhanced(self, file_path: str, tpa_id: str) -> Dict[str, Any]:
        """Enhanced BPS extraction with document type specialization"""
        try:
            # First do standard extraction
            extracted_data = await self.extract_bps_data(file_path)
            
            # Then enhance with AI-powered structure analysis
            if self.ai_service:
                enhanced_data = await self._enhance_bps_structure_analysis(extracted_data, tpa_id)
                extracted_data.update(enhanced_data)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Enhanced BPS extraction failed: {e}")
            # Fallback to standard extraction
            return await self.extract_bps_data(file_path)
    
    async def _enhance_bps_structure_analysis(self, extracted_data: Dict[str, Any], tpa_id: str) -> Dict[str, Any]:
        """Enhance BPS structure analysis with AI"""
        try:
            benefits = extracted_data.get('benefits', [])
            if not benefits:
                return {}
            
            # Sample benefits for analysis
            sample_benefits = benefits[:10]  # First 10 benefits
            benefit_summaries = []
            
            for benefit in sample_benefits:
                summary = f"{benefit.get('description', '')}: {benefit.get('in_network_coverage', {})} / {benefit.get('out_of_network_coverage', {})}"
                benefit_summaries.append(summary)
            
            analysis_prompt = f"""
            Analyze this BPS (Benefit Payment Schedule) structure and enhance understanding:
            
            Sample Benefits:
            {chr(10).join(benefit_summaries[:5])}
            
            Total Benefits: {len(benefits)}
            
            Provide enhanced analysis in JSON format:
            {{
                "structure_analysis": {{
                    "benefit_categories_found": ["medical", "pharmacy"],
                    "coverage_tiers": ["in_network", "out_of_network"],
                    "payment_types": ["copay", "coinsurance", "deductible"]
                }},
                "cross_reference_opportunities": [
                    {{
                        "benefit_type": "primary_care",
                        "spd_section_likely": "physician_services",
                        "connection_strength": 0.9
                    }}
                ],
                "data_quality_assessment": {{
                    "completeness_score": 0.85,
                    "consistency_score": 0.90,
                    "standardization_score": 0.75
                }},
                "enhancement_recommendations": ["standardize_amounts", "categorize_benefits"]
            }}
            """
            
            ai_response = await self.ai_service.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                model="gpt-4o-mini",
                max_tokens=600,
                temperature=0.1
            )
            
            enhancement = json.loads(ai_response.content)
            
            return {
                'enhanced_structure': enhancement.get('structure_analysis', {}),
                'cross_reference_opportunities': enhancement.get('cross_reference_opportunities', []),
                'data_quality': enhancement.get('data_quality_assessment', {}),
                'enhancement_recommendations': enhancement.get('enhancement_recommendations', [])
            }
            
        except Exception as e:
            logger.warning(f"BPS structure analysis enhancement failed: {e}")
            return {}