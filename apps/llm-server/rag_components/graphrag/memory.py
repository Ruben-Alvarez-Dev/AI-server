"""
GraphRAG Memory System
Knowledge Graph + Retrieval Augmented Generation with temporal awareness
Based on Microsoft GraphRAG research
"""

import asyncio
import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import pickle
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Knowledge graph entity"""
    id: str
    name: str
    type: str
    description: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    source_docs: List[str] = field(default_factory=list)

@dataclass
class Relationship:
    """Knowledge graph relationship"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    description: str
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_docs: List[str] = field(default_factory=list)

@dataclass
class Community:
    """Knowledge graph community (cluster)"""
    id: str
    entities: Set[str]
    title: str
    summary: str
    level: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    keywords: List[str] = field(default_factory=list)

class GraphRAGMemory:
    """
    Knowledge Graph Memory with RAG capabilities
    Combines entity extraction, community detection, and temporal awareness
    """
    
    def __init__(self, storage_path: str = "./data/graphrag"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.communities: Dict[str, Community] = {}
        self.temporal_index: Dict[str, List[str]] = {}  # date -> entity_ids
        
        # Configuration
        self.community_algorithm = "leiden"
        self.max_graph_depth = 4
        self.temporal_window_days = 7
        self.entity_similarity_threshold = 0.8
        
        # Prompts for entity extraction
        self.entity_extraction_prompt = """
Extract entities and relationships from the following text. Focus on:
- People, organizations, concepts, locations, events
- Relationships between entities
- Temporal information when available

Text: {text}

Return a JSON structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "PERSON|ORGANIZATION|CONCEPT|LOCATION|EVENT",
      "description": "brief description",
      "attributes": {{}}
    }}
  ],
  "relationships": [
    {{
      "source": "entity1",
      "target": "entity2", 
      "relation": "relationship type",
      "description": "relationship description",
      "strength": 0.0-1.0
    }}
  ]
}}
"""

        self.community_summary_prompt = """
Analyze the following cluster of related entities and relationships to create a summary.

Entities: {entities}
Relationships: {relationships}

Provide a JSON response:
{{
  "title": "concise title for this community",
  "summary": "comprehensive summary of the community",
  "keywords": ["key", "terms", "list"],
  "main_themes": ["theme1", "theme2"]
}}
"""

    async def ingest_document(
        self, 
        content: str, 
        document_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ingest document and extract knowledge graph elements
        """
        logger.info(f"Ingesting document: {document_id}")
        
        try:
            # Extract entities and relationships
            extraction_result = await self._extract_entities_relationships(content)
            
            entities_added = 0
            relationships_added = 0
            
            # Process entities
            for entity_data in extraction_result.get('entities', []):
                entity_id = await self._add_or_update_entity(
                    entity_data, 
                    document_id
                )
                if entity_id:
                    entities_added += 1
            
            # Process relationships
            for rel_data in extraction_result.get('relationships', []):
                rel_id = await self._add_or_update_relationship(
                    rel_data, 
                    document_id
                )
                if rel_id:
                    relationships_added += 1
            
            # Update communities
            await self._update_communities()
            
            # Save state
            await self._save_state()
            
            logger.info(f"Document {document_id} processed: {entities_added} entities, {relationships_added} relationships")
            
            return {
                'document_id': document_id,
                'entities_added': entities_added,
                'relationships_added': relationships_added,
                'total_entities': len(self.entities),
                'total_relationships': len(self.relationships)
            }
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return {'error': str(e)}
    
    async def search_knowledge_graph(
        self, 
        query: str, 
        max_results: int = 10,
        include_communities: bool = True
    ) -> Dict[str, Any]:
        """
        Search knowledge graph using semantic similarity and graph traversal
        """
        logger.info(f"Searching knowledge graph: {query}")
        
        try:
            # Find relevant entities
            relevant_entities = await self._find_relevant_entities(query)
            
            # Expand through graph connections
            expanded_entities = await self._expand_entity_neighborhood(
                relevant_entities, 
                max_depth=self.max_graph_depth
            )
            
            # Find relevant communities
            relevant_communities = []
            if include_communities:
                relevant_communities = await self._find_relevant_communities(query)
            
            # Build context from entities and relationships
            context = await self._build_graph_context(expanded_entities, relevant_communities)
            
            return {
                'query': query,
                'entities_found': len(expanded_entities),
                'communities_found': len(relevant_communities),
                'context': context,
                'graph_paths': await self._find_connecting_paths(expanded_entities[:5])
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph search failed: {e}")
            return {'error': str(e)}
    
    async def get_temporal_context(
        self, 
        query: str, 
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get temporally-aware context for the query
        """
        if time_window is None:
            time_window = timedelta(days=self.temporal_window_days)
        
        cutoff_date = datetime.now() - time_window
        
        # Find entities updated within time window
        recent_entities = [
            entity for entity in self.entities.values()
            if entity.updated_at >= cutoff_date
        ]
        
        # Search within recent entities
        relevant_recent = []
        query_lower = query.lower()
        
        for entity in recent_entities:
            if (query_lower in entity.name.lower() or 
                query_lower in entity.description.lower()):
                relevant_recent.append(entity)
        
        return {
            'query': query,
            'time_window_days': time_window.days,
            'recent_entities': len(recent_entities),
            'relevant_recent': [
                {
                    'id': e.id,
                    'name': e.name,
                    'type': e.type,
                    'description': e.description,
                    'updated_at': e.updated_at.isoformat()
                } for e in relevant_recent[:10]
            ]
        }
    
    async def _extract_entities_relationships(self, text: str) -> Dict[str, Any]:
        """Extract entities and relationships from text using LLM"""
        
        prompt = self.entity_extraction_prompt.format(text=text[:2000])  # Limit text length
        
        try:
            # This will be integrated with main LLM
            # For now, return mock extraction
            return {
                'entities': [
                    {
                        'name': 'Example Entity',
                        'type': 'CONCEPT',
                        'description': 'Mock entity for testing',
                        'attributes': {}
                    }
                ],
                'relationships': [
                    {
                        'source': 'Example Entity',
                        'target': 'Related Concept',
                        'relation': 'relates_to',
                        'description': 'Mock relationship',
                        'strength': 0.8
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {'entities': [], 'relationships': []}
    
    async def _add_or_update_entity(self, entity_data: Dict, document_id: str) -> Optional[str]:
        """Add or update entity in knowledge graph"""
        
        entity_name = entity_data.get('name', '').strip()
        if not entity_name:
            return None
        
        # Generate entity ID
        entity_id = hashlib.md5(entity_name.lower().encode()).hexdigest()[:12]
        
        if entity_id in self.entities:
            # Update existing entity
            entity = self.entities[entity_id]
            entity.updated_at = datetime.now()
            entity.source_docs.append(document_id)
            
            # Merge attributes
            new_attributes = entity_data.get('attributes', {})
            entity.attributes.update(new_attributes)
            
        else:
            # Create new entity
            entity = Entity(
                id=entity_id,
                name=entity_name,
                type=entity_data.get('type', 'UNKNOWN'),
                description=entity_data.get('description', ''),
                attributes=entity_data.get('attributes', {}),
                source_docs=[document_id]
            )
            self.entities[entity_id] = entity
        
        # Add to graph
        self.graph.add_node(entity_id, **entity.__dict__)
        
        # Update temporal index
        date_key = entity.updated_at.date().isoformat()
        if date_key not in self.temporal_index:
            self.temporal_index[date_key] = []
        if entity_id not in self.temporal_index[date_key]:
            self.temporal_index[date_key].append(entity_id)
        
        return entity_id
    
    async def _add_or_update_relationship(self, rel_data: Dict, document_id: str) -> Optional[str]:
        """Add or update relationship in knowledge graph"""
        
        source_name = rel_data.get('source', '').strip()
        target_name = rel_data.get('target', '').strip()
        
        if not source_name or not target_name:
            return None
        
        # Get entity IDs
        source_id = hashlib.md5(source_name.lower().encode()).hexdigest()[:12]
        target_id = hashlib.md5(target_name.lower().encode()).hexdigest()[:12]
        
        # Generate relationship ID
        rel_id = hashlib.md5(f"{source_id}-{target_id}-{rel_data.get('relation', '')}".encode()).hexdigest()[:12]
        
        if rel_id in self.relationships:
            # Update existing relationship
            relationship = self.relationships[rel_id]
            relationship.updated_at = datetime.now()
            relationship.source_docs.append(document_id)
        else:
            # Create new relationship
            relationship = Relationship(
                id=rel_id,
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_data.get('relation', 'UNKNOWN'),
                description=rel_data.get('description', ''),
                strength=rel_data.get('strength', 1.0),
                source_docs=[document_id]
            )
            self.relationships[rel_id] = relationship
        
        # Add to graph
        if source_id in self.entities and target_id in self.entities:
            self.graph.add_edge(
                source_id, 
                target_id, 
                key=rel_id,
                **relationship.__dict__
            )
        
        return rel_id
    
    async def _update_communities(self):
        """Update community detection"""
        if len(self.graph.nodes()) < 3:
            return
        
        try:
            # Convert to undirected for community detection
            undirected_graph = self.graph.to_undirected()
            
            # Use simple clustering for now (can be enhanced with Leiden algorithm)
            communities_nodes = nx.community.greedy_modularity_communities(undirected_graph)
            
            # Update communities
            for i, community_nodes in enumerate(communities_nodes):
                if len(community_nodes) < 2:
                    continue
                
                community_id = f"community_{i}"
                
                if community_id in self.communities:
                    community = self.communities[community_id]
                    community.entities = set(community_nodes)
                else:
                    community = Community(
                        id=community_id,
                        entities=set(community_nodes),
                        title=f"Community {i+1}",
                        summary=f"Auto-detected community with {len(community_nodes)} entities"
                    )
                    self.communities[community_id] = community
                
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
    
    async def _find_relevant_entities(self, query: str) -> List[Entity]:
        """Find entities relevant to query"""
        relevant = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            # Simple relevance scoring
            score = 0.0
            
            if query_lower in entity.name.lower():
                score += 1.0
            if query_lower in entity.description.lower():
                score += 0.5
            
            # Check attributes
            for attr_value in entity.attributes.values():
                if isinstance(attr_value, str) and query_lower in attr_value.lower():
                    score += 0.3
            
            if score > 0:
                relevant.append((entity, score))
        
        # Sort by relevance and return top entities
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [entity for entity, score in relevant[:20]]
    
    async def _expand_entity_neighborhood(
        self, 
        entities: List[Entity], 
        max_depth: int = 2
    ) -> List[Entity]:
        """Expand entity list through graph connections"""
        expanded_ids = set(entity.id for entity in entities)
        
        for depth in range(max_depth):
            new_ids = set()
            
            for entity_id in list(expanded_ids):
                if entity_id in self.graph:
                    # Add neighbors
                    neighbors = list(self.graph.neighbors(entity_id))
                    new_ids.update(neighbors)
                    
                    # Add predecessors
                    predecessors = list(self.graph.predecessors(entity_id))
                    new_ids.update(predecessors)
            
            expanded_ids.update(new_ids)
        
        # Return entity objects
        return [self.entities[eid] for eid in expanded_ids if eid in self.entities]
    
    async def _find_relevant_communities(self, query: str) -> List[Community]:
        """Find communities relevant to query"""
        relevant = []
        query_lower = query.lower()
        
        for community in self.communities.values():
            score = 0.0
            
            if query_lower in community.title.lower():
                score += 1.0
            if query_lower in community.summary.lower():
                score += 0.5
            
            for keyword in community.keywords:
                if query_lower in keyword.lower():
                    score += 0.3
            
            if score > 0:
                relevant.append((community, score))
        
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [community for community, score in relevant[:5]]
    
    async def _build_graph_context(
        self, 
        entities: List[Entity], 
        communities: List[Community]
    ) -> str:
        """Build context string from graph elements"""
        
        context_parts = []
        
        # Add entity information
        if entities:
            context_parts.append("## Entities:")
            for entity in entities[:10]:  # Limit to top 10
                context_parts.append(f"- **{entity.name}** ({entity.type}): {entity.description}")
        
        # Add relationship information
        if len(entities) > 1:
            context_parts.append("\n## Relationships:")
            entity_ids = [e.id for e in entities[:10]]
            
            for rel in self.relationships.values():
                if rel.source_id in entity_ids and rel.target_id in entity_ids:
                    source_name = self.entities.get(rel.source_id, Entity(id="", name="Unknown", type="", description="")).name
                    target_name = self.entities.get(rel.target_id, Entity(id="", name="Unknown", type="", description="")).name
                    context_parts.append(f"- {source_name} --({rel.relation_type})--> {target_name}")
        
        # Add community summaries
        if communities:
            context_parts.append("\n## Community Context:")
            for community in communities:
                context_parts.append(f"- **{community.title}**: {community.summary}")
        
        return "\n".join(context_parts)
    
    async def _find_connecting_paths(self, entities: List[Entity]) -> List[List[str]]:
        """Find paths connecting entities in the graph"""
        if len(entities) < 2:
            return []
        
        paths = []
        entity_ids = [e.id for e in entities]
        
        try:
            for i, source_id in enumerate(entity_ids):
                for target_id in entity_ids[i+1:]:
                    if source_id in self.graph and target_id in self.graph:
                        try:
                            path = nx.shortest_path(self.graph, source_id, target_id)
                            if len(path) <= 4:  # Only short paths
                                path_names = [self.entities.get(eid, Entity(id="", name="Unknown", type="", description="")).name for eid in path]
                                paths.append(path_names)
                        except nx.NetworkXNoPath:
                            continue
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
        
        return paths[:5]  # Limit to 5 paths
    
    async def _save_state(self):
        """Save current state to disk"""
        try:
            # Save entities
            entities_file = self.storage_path / "entities.json"
            with open(entities_file, 'w') as f:
                entities_data = {
                    eid: {
                        **entity.__dict__,
                        'created_at': entity.created_at.isoformat(),
                        'updated_at': entity.updated_at.isoformat()
                    } for eid, entity in self.entities.items()
                }
                json.dump(entities_data, f, indent=2)
            
            # Save relationships
            relationships_file = self.storage_path / "relationships.json"
            with open(relationships_file, 'w') as f:
                rels_data = {
                    rid: {
                        **rel.__dict__,
                        'created_at': rel.created_at.isoformat(),
                        'updated_at': rel.updated_at.isoformat()
                    } for rid, rel in self.relationships.items()
                }
                json.dump(rels_data, f, indent=2)
            
            # Save graph
            graph_file = self.storage_path / "graph.pickle"
            with open(graph_file, 'wb') as f:
                pickle.dump(self.graph, f)
                
        except Exception as e:
            logger.error(f"Save state failed: {e}")
    
    async def load_state(self):
        """Load state from disk"""
        try:
            # Load entities
            entities_file = self.storage_path / "entities.json"
            if entities_file.exists():
                with open(entities_file, 'r') as f:
                    entities_data = json.load(f)
                    
                for eid, data in entities_data.items():
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self.entities[eid] = Entity(**data)
            
            # Load relationships
            relationships_file = self.storage_path / "relationships.json"
            if relationships_file.exists():
                with open(relationships_file, 'r') as f:
                    rels_data = json.load(f)
                    
                for rid, data in rels_data.items():
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self.relationships[rid] = Relationship(**data)
            
            # Load graph
            graph_file = self.storage_path / "graph.pickle"
            if graph_file.exists():
                with open(graph_file, 'rb') as f:
                    self.graph = pickle.load(f)
            
            logger.info(f"Loaded {len(self.entities)} entities, {len(self.relationships)} relationships")
            
        except Exception as e:
            logger.error(f"Load state failed: {e}")

# Export
__all__ = ['GraphRAGMemory', 'Entity', 'Relationship', 'Community']