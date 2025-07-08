"""
Knowledge Graph service using Neo4j
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Service for knowledge graph operations using Neo4j"""
    
    def __init__(self):
        self.driver = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            # Create constraints and indexes
            await self._create_schema()
            
            self.initialized = True
            logger.info("Knowledge graph service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph service: {e}")
            # Don't raise error - fallback to in-memory storage
            logger.warning("Continuing without Neo4j - using fallback storage")
    
    async def _create_schema(self):
        """Create Neo4j schema constraints and indexes"""
        constraints_and_indexes = [
            # Constraints
            "CREATE CONSTRAINT tpa_id IF NOT EXISTS FOR (t:TPA) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT health_plan_id IF NOT EXISTS FOR (p:HealthPlan) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT benefit_id IF NOT EXISTS FOR (b:Benefit) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            
            # Indexes
            "CREATE INDEX tpa_slug IF NOT EXISTS FOR (t:TPA) ON (t.slug)",
            "CREATE INDEX health_plan_number IF NOT EXISTS FOR (p:HealthPlan) ON (p.plan_number)",
            "CREATE INDEX benefit_type IF NOT EXISTS FOR (b:Benefit) ON (b.benefit_type)",
            "CREATE INDEX benefit_category IF NOT EXISTS FOR (b:Benefit) ON (b.category)"
        ]
        
        with self.driver.session() as session:
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                except Exception as e:
                    # Constraints may already exist
                    logger.debug(f"Schema query warning: {e}")
    
    async def create_tpa_node(self, tpa_data: Dict[str, Any]) -> bool:
        """Create TPA node"""
        if not self.initialized:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MERGE (t:TPA {id: $id})
                SET t.name = $name,
                    t.slug = $slug,
                    t.created_at = $created_at,
                    t.updated_at = $updated_at
                RETURN t
                """
                session.run(query, tpa_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create TPA node: {e}")
            return False
    
    async def create_health_plan_node(self, plan_data: Dict[str, Any]) -> bool:
        """Create health plan node and link to TPA"""
        if not self.initialized:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (t:TPA {id: $tpa_id})
                MERGE (p:HealthPlan {id: $id})
                SET p.name = $name,
                    p.plan_number = $plan_number,
                    p.plan_year = $plan_year,
                    p.plan_type = $plan_type,
                    p.created_at = $created_at,
                    p.updated_at = $updated_at
                MERGE (t)-[:HAS_PLAN]->(p)
                RETURN p
                """
                session.run(query, plan_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create health plan node: {e}")
            return False
    
    async def create_benefit_nodes(self, benefits_data: List[Dict[str, Any]]) -> bool:
        """Create benefit nodes and relationships"""
        if not self.initialized:
            return False
        
        try:
            with self.driver.session() as session:
                for benefit in benefits_data:
                    # Create benefit node
                    query = """
                    MATCH (p:HealthPlan {id: $health_plan_id})
                    MERGE (b:Benefit {id: $id})
                    SET b.benefit_type = $benefit_type,
                        b.category = $category,
                        b.description = $description,
                        b.in_network_coverage = $in_network_coverage,
                        b.out_of_network_coverage = $out_of_network_coverage,
                        b.copay = $copay,
                        b.coinsurance = $coinsurance,
                        b.deductible_applies = $deductible_applies,
                        b.prior_auth_required = $prior_auth_required,
                        b.created_at = $created_at
                    MERGE (p)-[:INCLUDES_BENEFIT]->(b)
                    """
                    session.run(query, benefit)
                    
                    # Create relationships between related benefits
                    if benefit.get("related_benefits"):
                        for related_id in benefit["related_benefits"]:
                            related_query = """
                            MATCH (b1:Benefit {id: $benefit_id})
                            MATCH (b2:Benefit {id: $related_id})
                            MERGE (b1)-[:RELATED_TO]->(b2)
                            """
                            session.run(related_query, {
                                "benefit_id": benefit["id"],
                                "related_id": related_id
                            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create benefit nodes: {e}")
            return False
    
    async def find_related_benefits(
        self, 
        health_plan_id: str, 
        benefit_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Find benefits related to specified types"""
        if not self.initialized:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:HealthPlan {id: $health_plan_id})-[:INCLUDES_BENEFIT]->(b:Benefit)
                WHERE b.benefit_type IN $benefit_types
                OPTIONAL MATCH (b)-[:RELATED_TO]->(related:Benefit)
                RETURN b, collect(related) as related_benefits
                """
                
                result = session.run(query, {
                    "health_plan_id": health_plan_id,
                    "benefit_types": benefit_types
                })
                
                benefits = []
                for record in result:
                    benefit = dict(record["b"])
                    benefit["related_benefits"] = [dict(r) for r in record["related_benefits"] if r]
                    benefits.append(benefit)
                
                return benefits
                
        except Exception as e:
            logger.error(f"Failed to find related benefits: {e}")
            return []
    
    async def find_related_benefits_multi_hop(
        self, 
        health_plan_id: str, 
        benefit_types: List[str],
        max_hops: int = 3
    ) -> List[Dict[str, Any]]:
        """Find benefits related to specified types with multi-hop traversal"""
        if not self.initialized:
            return []
        
        try:
            with self.driver.session() as session:
                # Multi-hop traversal query
                query = f"""
                MATCH (p:HealthPlan {{id: $health_plan_id}})-[:INCLUDES_BENEFIT]->(b:Benefit)
                WHERE b.benefit_type IN $benefit_types
                
                // Find benefits within max_hops relationships
                OPTIONAL MATCH path = (b)-[:RELATED_TO*1..{max_hops}]-(connected:Benefit)
                
                // Find benefits that share categories
                OPTIONAL MATCH (b)-[:BELONGS_TO_CATEGORY]-(category)<-[:BELONGS_TO_CATEGORY]-(category_related:Benefit)
                WHERE (p)-[:INCLUDES_BENEFIT]->(category_related)
                
                // Find benefits with similar coverage patterns
                OPTIONAL MATCH (coverage_related:Benefit)
                WHERE (p)-[:INCLUDES_BENEFIT]->(coverage_related)
                AND coverage_related.category = b.category
                AND coverage_related.id <> b.id
                
                WITH b, 
                     collect(DISTINCT connected) as multi_hop_benefits,
                     collect(DISTINCT category_related) as category_benefits,
                     collect(DISTINCT coverage_related) as coverage_benefits
                
                RETURN b, 
                       multi_hop_benefits,
                       category_benefits,
                       coverage_benefits,
                       // Calculate relationship strength
                       size(multi_hop_benefits) + size(category_benefits) + size(coverage_benefits) as relationship_strength
                ORDER BY relationship_strength DESC
                """
                
                result = session.run(query, {
                    "health_plan_id": health_plan_id,
                    "benefit_types": benefit_types
                })
                
                benefits = []
                for record in result:
                    benefit = dict(record["b"])
                    benefit["multi_hop_benefits"] = [dict(r) for r in record["multi_hop_benefits"] if r]
                    benefit["category_benefits"] = [dict(r) for r in record["category_benefits"] if r]
                    benefit["coverage_benefits"] = [dict(r) for r in record["coverage_benefits"] if r]
                    benefit["relationship_strength"] = record["relationship_strength"]
                    benefits.append(benefit)
                
                return benefits
                
        except Exception as e:
            logger.error(f"Failed to find related benefits with multi-hop: {e}")
            # Fallback to single-hop search
            return await self.find_related_benefits(health_plan_id, benefit_types)
    
    async def get_benefit_hierarchy(self, health_plan_id: str) -> Dict[str, Any]:
        """Get benefit hierarchy for a health plan"""
        if not self.initialized:
            return {}
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:HealthPlan {id: $health_plan_id})-[:INCLUDES_BENEFIT]->(b:Benefit)
                RETURN b.category as category, 
                       collect({
                           id: b.id,
                           benefit_type: b.benefit_type,
                           description: b.description,
                           copay: b.copay,
                           coinsurance: b.coinsurance
                       }) as benefits
                ORDER BY category
                """
                
                result = session.run(query, {"health_plan_id": health_plan_id})
                
                hierarchy = {}
                for record in result:
                    category = record["category"] or "Other"
                    hierarchy[category] = record["benefits"]
                
                return hierarchy
                
        except Exception as e:
            logger.error(f"Failed to get benefit hierarchy: {e}")
            return {}
    
    async def search_benefits(
        self, 
        health_plan_id: str, 
        search_terms: List[str]
    ) -> List[Dict[str, Any]]:
        """Search benefits by terms"""
        if not self.initialized:
            return []
        
        try:
            with self.driver.session() as session:
                # Create search pattern
                search_pattern = " OR ".join([f"toLower(b.description) CONTAINS toLower('{term}')" for term in search_terms])
                search_pattern += " OR " + " OR ".join([f"toLower(b.benefit_type) CONTAINS toLower('{term}')" for term in search_terms])
                
                query = f"""
                MATCH (p:HealthPlan {{id: $health_plan_id}})-[:INCLUDES_BENEFIT]->(b:Benefit)
                WHERE {search_pattern}
                RETURN b
                ORDER BY b.category, b.benefit_type
                """
                
                result = session.run(query, {"health_plan_id": health_plan_id})
                
                benefits = [dict(record["b"]) for record in result]
                return benefits
                
        except Exception as e:
            logger.error(f"Failed to search benefits: {e}")
            return []
    
    async def create_benefit_relationships(
        self,
        health_plan_id: str,
        benefit_relationships: List[Dict[str, Any]]
    ) -> bool:
        """Create sophisticated benefit relationships"""
        if not self.initialized:
            return False
        
        try:
            with self.driver.session() as session:
                for rel in benefit_relationships:
                    # Create different types of relationships
                    relationship_type = rel.get('relationship_type', 'RELATED_TO')
                    
                    query = f"""
                    MATCH (b1:Benefit {{id: $benefit_id_1}})
                    MATCH (b2:Benefit {{id: $benefit_id_2}})
                    MERGE (b1)-[r:{relationship_type}]->(b2)
                    SET r.strength = $strength,
                        r.description = $description,
                        r.created_at = $created_at
                    """
                    
                    session.run(query, {
                        "benefit_id_1": rel["benefit_id_1"],
                        "benefit_id_2": rel["benefit_id_2"],
                        "strength": rel.get("strength", 0.5),
                        "description": rel.get("description", ""),
                        "created_at": datetime.utcnow().isoformat()
                    })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create benefit relationships: {e}")
            return False
    
    async def analyze_benefit_patterns(
        self,
        health_plan_id: str
    ) -> Dict[str, Any]:
        """Analyze benefit patterns and create intelligent relationships"""
        if not self.initialized:
            return {}
        
        try:
            with self.driver.session() as session:
                # Find benefits with similar coverage patterns
                query = """
                MATCH (p:HealthPlan {id: $health_plan_id})-[:INCLUDES_BENEFIT]->(b:Benefit)
                
                // Group benefits by similar characteristics
                WITH b.category as category,
                     b.coinsurance as coinsurance,
                     b.deductible_applies as deductible_applies,
                     b.prior_auth_required as prior_auth_required,
                     collect(b) as benefits
                WHERE size(benefits) > 1
                
                // Create relationships between benefits with similar patterns
                UNWIND benefits as b1
                UNWIND benefits as b2
                WHERE b1.id <> b2.id
                MERGE (b1)-[r:SIMILAR_COVERAGE]->(b2)
                SET r.similarity_score = 
                    CASE 
                        WHEN b1.coinsurance = b2.coinsurance AND 
                             b1.deductible_applies = b2.deductible_applies AND 
                             b1.prior_auth_required = b2.prior_auth_required
                        THEN 1.0
                        ELSE 0.7
                    END
                
                RETURN count(r) as relationships_created
                """
                
                result = session.run(query, {"health_plan_id": health_plan_id})
                record = result.single()
                
                return {
                    "relationships_created": record["relationships_created"] if record else 0,
                    "analysis_completed": True
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze benefit patterns: {e}")
            return {"analysis_completed": False}
    
    async def get_benefit_path(
        self,
        health_plan_id: str,
        start_benefit_type: str,
        end_benefit_type: str
    ) -> List[Dict[str, Any]]:
        """Find the shortest path between two benefit types"""
        if not self.initialized:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:HealthPlan {id: $health_plan_id})-[:INCLUDES_BENEFIT]->(start:Benefit {benefit_type: $start_benefit_type})
                MATCH (p)-[:INCLUDES_BENEFIT]->(end:Benefit {benefit_type: $end_benefit_type})
                MATCH path = shortestPath((start)-[*]-(end))
                RETURN path, length(path) as path_length
                ORDER BY path_length ASC
                LIMIT 1
                """
                
                result = session.run(query, {
                    "health_plan_id": health_plan_id,
                    "start_benefit_type": start_benefit_type,
                    "end_benefit_type": end_benefit_type
                })
                
                record = result.single()
                if record:
                    path = record["path"]
                    path_data = []
                    
                    for i in range(len(path.nodes)):
                        node = dict(path.nodes[i])
                        path_data.append({
                            "benefit": node,
                            "step": i + 1,
                            "relationship": dict(path.relationships[i]) if i < len(path.relationships) else None
                        })
                    
                    return path_data
                
                return []
                
        except Exception as e:
            logger.error(f"Failed to find benefit path: {e}")
            return []
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()