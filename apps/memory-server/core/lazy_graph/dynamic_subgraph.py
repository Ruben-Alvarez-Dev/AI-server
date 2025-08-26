"""
Dynamic Subgraph Builder - Core of LazyGraphRAG
Builds knowledge subgraphs on-demand from document candidates
"""

import asyncio
import networkx as nx
import spacy
import time
from typing import List, Set, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import re

from .lazy_indexer import Document
from core.config import get_config
from core.logging_config import get_logger, get_performance_logger

# Setup loggers
logger = get_logger("dynamic-subgraph")
perf_logger = get_performance_logger("dynamic-subgraph")


class DynamicSubgraphBuilder:
    """
    Dynamic Knowledge Subgraph Builder
    
    Constructs graphs on-demand from document candidates without pre-processing
    Key to LazyGraphRAG's zero-cost indexing approach
    """
    
    def __init__(self, nlp_model: Optional[spacy.Language] = None):
        self.config = get_config()
        
        # Initialize spaCy model
        if nlp_model is None:
            self._initialize_nlp_model()
        else:
            self.nlp = nlp_model
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.NUM_WORKERS)
        
        # Entity extraction patterns and filters
        self.entity_types = {
            'PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 
            'LAW', 'LANGUAGE', 'NORP', 'FAC', 'LOC'
        }
        
        # Relationship extraction patterns
        self.relation_patterns = [
            # Subject-Verb-Object patterns
            (r'\b(\w+(?:\s+\w+)*)\s+(is|are|was|were|becomes?|became)\s+(\w+(?:\s+\w+)*)', 'IS_A'),
            (r'\b(\w+(?:\s+\w+)*)\s+(works?\s+(?:at|for)|employed\s+by)\s+(\w+(?:\s+\w+)*)', 'WORKS_FOR'),
            (r'\b(\w+(?:\s+\w+)*)\s+(founded|created|established)\s+(\w+(?:\s+\w+)*)', 'FOUNDED'),
            (r'\b(\w+(?:\s+\w+)*)\s+(located\s+in|based\s+in|from)\s+(\w+(?:\s+\w+)*)', 'LOCATED_IN'),
            (r'\b(\w+(?:\s+\w+)*)\s+(part\s+of|member\s+of|belongs\s+to)\s+(\w+(?:\s+\w+)*)', 'PART_OF'),
        ]
        
        # Performance tracking
        self.stats = {
            'subgraphs_built': 0,
            'entities_extracted': 0,
            'relations_extracted': 0,
            'build_time': 0.0
        }
    
    def _initialize_nlp_model(self):
        """Initialize spaCy NLP model"""
        try:
            logger.info("Loading spaCy model for entity extraction")
            self.nlp = spacy.load("en_core_web_lg")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("Large spaCy model not found, falling back to small model")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.error("No spaCy model found, entity extraction will be limited")
                self.nlp = None
    
    async def build_subgraph(
        self, 
        documents: List[Document], 
        query: str,
        max_entities: int = 100,
        max_relations: int = 200
    ) -> nx.Graph:
        """
        Build dynamic knowledge subgraph from document candidates
        
        Args:
            documents: Candidate documents from vector search
            query: Original query for context-aware extraction
            max_entities: Maximum entities to extract
            max_relations: Maximum relations to extract
        
        Returns:
            NetworkX graph representing the knowledge subgraph
        """
        start_time = time.time()
        
        logger.info(
            "Building dynamic subgraph",
            doc_count=len(documents),
            query_length=len(query)
        )
        
        try:
            # Extract entities and relations from all documents in parallel
            extraction_tasks = [
                self._extract_entities_and_relations(doc, query) 
                for doc in documents
            ]
            
            extractions = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            # Process extractions and build graph
            graph = nx.Graph()
            all_entities = []
            all_relations = []
            
            for i, extraction in enumerate(extractions):
                if isinstance(extraction, Exception):
                    logger.error(f"Entity extraction failed for document {documents[i].id}: {extraction}")
                    continue
                
                entities, relations = extraction
                all_entities.extend(entities)
                all_relations.extend(relations)
            
            # Filter and rank entities/relations
            top_entities = self._rank_and_filter_entities(all_entities, query, max_entities)
            top_relations = self._rank_and_filter_relations(all_relations, top_entities, max_relations)
            
            # Build graph
            self._build_graph_from_extractions(graph, top_entities, top_relations, documents)
            
            # Add query context to graph
            await self._enhance_graph_with_query_context(graph, query)
            
            build_time = time.time() - start_time
            
            # Update stats
            self.stats['subgraphs_built'] += 1
            self.stats['entities_extracted'] += len(top_entities)
            self.stats['relations_extracted'] += len(top_relations)
            self.stats['build_time'] += build_time
            
            perf_logger.log_timing(
                "subgraph_build",
                build_time,
                documents=len(documents),
                nodes=graph.number_of_nodes(),
                edges=graph.number_of_edges()
            )
            
            logger.info(
                "Dynamic subgraph built successfully",
                nodes=graph.number_of_nodes(),
                edges=graph.number_of_edges(),
                build_time_ms=round(build_time * 1000, 2)
            )
            
            return graph
            
        except Exception as e:
            logger.error(f"Failed to build dynamic subgraph: {e}")
            # Return empty graph as fallback
            return nx.Graph()
    
    async def _extract_entities_and_relations(
        self, 
        document: Document, 
        query: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities and relations from a single document
        
        Returns:
            Tuple of (entities, relations)
        """
        try:
            # Limit content length for processing
            content = document.content[:50000]  # 50K char limit
            
            if not self.nlp:
                return await self._fallback_extraction(content, document)
            
            # Process with spaCy in thread pool
            loop = asyncio.get_event_loop()
            doc_nlp = await loop.run_in_executor(
                self.executor,
                lambda: self.nlp(content)
            )
            
            # Extract named entities
            entities = []
            entity_positions = {}
            
            for ent in doc_nlp.ents:
                if ent.label_ in self.entity_types and len(ent.text.strip()) > 2:
                    entity_info = {
                        'text': ent.text.strip(),
                        'label': ent.label_,
                        'confidence': 0.8,  # Base confidence
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'doc_id': document.id,
                        'context': content[max(0, ent.start_char-50):ent.end_char+50]
                    }
                    entities.append(entity_info)
                    entity_positions[ent.text.strip()] = (ent.start_char, ent.end_char)
            
            # Extract relations using patterns and dependency parsing
            relations = []
            
            # Pattern-based relation extraction
            pattern_relations = await self._extract_pattern_relations(content, entity_positions)
            relations.extend(pattern_relations)
            
            # Dependency-based relation extraction
            dependency_relations = await self._extract_dependency_relations(doc_nlp, entity_positions)
            relations.extend(dependency_relations)
            
            # Add document metadata to entities
            for entity in entities:
                entity['source_similarity'] = document.metadata.get('similarity_score', 0.0)
                entity['query_relevance'] = self._calculate_query_relevance(entity['text'], query)
            
            # Add document metadata to relations
            for relation in relations:
                relation['doc_id'] = document.id
                relation['source_similarity'] = document.metadata.get('similarity_score', 0.0)
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"Entity extraction failed for document {document.id}: {e}")
            return [], []
    
    async def _fallback_extraction(self, content: str, document: Document) -> Tuple[List[Dict], List[Dict]]:
        """Fallback extraction without spaCy"""
        logger.warning("Using fallback entity extraction")
        
        # Simple regex-based entity extraction
        entities = []
        
        # Extract potential organizations (capitalized words)
        org_pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b'
        for match in re.finditer(org_pattern, content):
            if 3 <= len(match.group()) <= 50:  # Reasonable length
                entities.append({
                    'text': match.group(),
                    'label': 'ORG',
                    'confidence': 0.5,
                    'start': match.start(),
                    'end': match.end(),
                    'doc_id': document.id,
                    'context': content[max(0, match.start()-50):match.end()+50]
                })
        
        # Extract potential locations
        location_indicators = ['in', 'at', 'from', 'located', 'based']
        for indicator in location_indicators:
            pattern = rf'\b{indicator}\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
            for match in re.finditer(pattern, content):
                location = match.group(1)
                if 2 <= len(location) <= 30:
                    entities.append({
                        'text': location,
                        'label': 'GPE',
                        'confidence': 0.4,
                        'start': match.start(1),
                        'end': match.end(1),
                        'doc_id': document.id,
                        'context': content[max(0, match.start()-50):match.end()+50]
                    })
        
        return entities, []  # No relations in fallback mode
    
    async def _extract_pattern_relations(
        self, 
        content: str, 
        entity_positions: Dict[str, Tuple[int, int]]
    ) -> List[Dict[str, Any]]:
        """Extract relations using regex patterns"""
        relations = []
        
        for pattern, relation_type in self.relation_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                subject = match.group(1).strip()
                predicate = match.group(2).strip()
                obj = match.group(3).strip()
                
                # Check if subject and object are entities
                if (subject in entity_positions and 
                    obj in entity_positions and 
                    subject != obj):
                    
                    relations.append({
                        'source': subject,
                        'target': obj,
                        'type': relation_type,
                        'predicate': predicate,
                        'confidence': 0.7,
                        'start': match.start(),
                        'end': match.end(),
                        'context': content[max(0, match.start()-100):match.end()+100]
                    })
        
        return relations
    
    async def _extract_dependency_relations(
        self, 
        doc_nlp, 
        entity_positions: Dict[str, Tuple[int, int]]
    ) -> List[Dict[str, Any]]:
        """Extract relations using dependency parsing"""
        relations = []
        
        try:
            # Find verb-based relations
            for token in doc_nlp:
                if token.pos_ == "VERB" and token.dep_ == "ROOT":
                    # Find subject and object dependencies
                    subjects = [child for child in token.children if child.dep_ in ["nsubj", "nsubjpass"]]
                    objects = [child for child in token.children if child.dep_ in ["dobj", "pobj", "attr"]]
                    
                    for subj in subjects:
                        for obj in objects:
                            # Find entities that contain these tokens
                            subj_entity = self._find_entity_for_token(subj, entity_positions)
                            obj_entity = self._find_entity_for_token(obj, entity_positions)
                            
                            if subj_entity and obj_entity and subj_entity != obj_entity:
                                relations.append({
                                    'source': subj_entity,
                                    'target': obj_entity,
                                    'type': token.lemma_.upper(),
                                    'predicate': token.text,
                                    'confidence': 0.6,
                                    'method': 'dependency_parsing'
                                })
            
            return relations
            
        except Exception as e:
            logger.error(f"Dependency relation extraction failed: {e}")
            return []
    
    def _find_entity_for_token(self, token, entity_positions: Dict[str, Tuple[int, int]]) -> Optional[str]:
        """Find entity that contains the given token"""
        token_start, token_end = token.idx, token.idx + len(token.text)
        
        for entity_text, (ent_start, ent_end) in entity_positions.items():
            if ent_start <= token_start < ent_end:
                return entity_text
        
        return None
    
    def _rank_and_filter_entities(
        self, 
        entities: List[Dict[str, Any]], 
        query: str, 
        max_entities: int
    ) -> List[Dict[str, Any]]:
        """Rank and filter entities by relevance"""
        if not entities:
            return []
        
        # Calculate composite scores
        for entity in entities:
            score = 0.0
            
            # Base confidence
            score += entity.get('confidence', 0.0) * 0.3
            
            # Source document similarity
            score += entity.get('source_similarity', 0.0) * 0.3
            
            # Query relevance
            score += entity.get('query_relevance', 0.0) * 0.4
            
            entity['composite_score'] = score
        
        # Remove duplicates (same text)
        unique_entities = {}
        for entity in entities:
            text = entity['text'].lower()
            if text not in unique_entities or entity['composite_score'] > unique_entities[text]['composite_score']:
                unique_entities[text] = entity
        
        # Sort by composite score
        ranked_entities = sorted(unique_entities.values(), key=lambda x: x['composite_score'], reverse=True)
        
        return ranked_entities[:max_entities]
    
    def _rank_and_filter_relations(
        self, 
        relations: List[Dict[str, Any]], 
        entities: List[Dict[str, Any]], 
        max_relations: int
    ) -> List[Dict[str, Any]]:
        """Rank and filter relations by relevance"""
        if not relations:
            return []
        
        # Create entity text set for filtering
        entity_texts = {entity['text'] for entity in entities}
        
        # Filter relations that connect ranked entities
        valid_relations = []
        for relation in relations:
            if (relation['source'] in entity_texts and 
                relation['target'] in entity_texts):
                
                # Calculate relation score
                score = relation.get('confidence', 0.0) * 0.5
                score += relation.get('source_similarity', 0.0) * 0.5
                
                relation['composite_score'] = score
                valid_relations.append(relation)
        
        # Remove duplicate relations
        unique_relations = {}
        for relation in valid_relations:
            key = (relation['source'], relation['target'], relation['type'])
            if key not in unique_relations or relation['composite_score'] > unique_relations[key]['composite_score']:
                unique_relations[key] = relation
        
        # Sort by composite score
        ranked_relations = sorted(unique_relations.values(), key=lambda x: x['composite_score'], reverse=True)
        
        return ranked_relations[:max_relations]
    
    def _build_graph_from_extractions(
        self, 
        graph: nx.Graph, 
        entities: List[Dict[str, Any]], 
        relations: List[Dict[str, Any]],
        documents: List[Document]
    ):
        """Build NetworkX graph from entities and relations"""
        # Add entity nodes
        for entity in entities:
            graph.add_node(
                entity['text'],
                type='entity',
                label=entity['label'],
                confidence=entity['confidence'],
                doc_id=entity['doc_id'],
                context=entity.get('context', ''),
                composite_score=entity.get('composite_score', 0.0)
            )
        
        # Add relation edges
        for relation in relations:
            if graph.has_node(relation['source']) and graph.has_node(relation['target']):
                graph.add_edge(
                    relation['source'],
                    relation['target'],
                    type='relation',
                    relation_type=relation['type'],
                    predicate=relation.get('predicate', ''),
                    confidence=relation['confidence'],
                    doc_id=relation.get('doc_id'),
                    context=relation.get('context', ''),
                    composite_score=relation.get('composite_score', 0.0)
                )
        
        # Add document nodes for provenance
        for doc in documents:
            if doc.metadata.get('similarity_score', 0) > 0.5:  # Only high-relevance docs
                graph.add_node(
                    f"doc_{doc.id}",
                    type='document',
                    doc_id=doc.id,
                    title=doc.metadata.get('title', 'Unknown'),
                    similarity_score=doc.metadata.get('similarity_score', 0.0)
                )
                
                # Connect document to its entities
                for entity in entities:
                    if entity['doc_id'] == doc.id and graph.has_node(entity['text']):
                        graph.add_edge(
                            f"doc_{doc.id}",
                            entity['text'],
                            type='contains',
                            confidence=1.0
                        )
    
    async def _enhance_graph_with_query_context(self, graph: nx.Graph, query: str):
        """Enhance graph with query-specific context"""
        try:
            # Extract key terms from query
            query_terms = self._extract_query_terms(query)
            
            # Add query context node
            if query_terms:
                graph.add_node(
                    "__query__",
                    type='query',
                    text=query,
                    terms=query_terms
                )
                
                # Connect query to relevant entities
                for node in graph.nodes():
                    if graph.nodes[node].get('type') == 'entity':
                        relevance = self._calculate_query_relevance(node, query)
                        if relevance > 0.3:
                            graph.add_edge(
                                "__query__",
                                node,
                                type='query_relevant',
                                relevance=relevance
                            )
        
        except Exception as e:
            logger.error(f"Failed to enhance graph with query context: {e}")
    
    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        # Simple keyword extraction
        import re
        
        # Remove stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 'where', 'why'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        
        # Filter stop words
        key_terms = [word for word in words if word not in stop_words]
        
        return key_terms[:10]  # Top 10 terms
    
    def _calculate_query_relevance(self, text: str, query: str) -> float:
        """Calculate relevance between text and query"""
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Simple word overlap scoring
        text_words = set(text_lower.split())
        query_words = set(query_lower.split())
        
        if not query_words:
            return 0.0
        
        overlap = len(text_words.intersection(query_words))
        relevance = overlap / len(query_words)
        
        # Boost for exact substring matches
        if text_lower in query_lower or query_lower in text_lower:
            relevance += 0.3
        
        return min(relevance, 1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get builder statistics"""
        return {
            **self.stats,
            'avg_build_time': self.stats['build_time'] / max(self.stats['subgraphs_built'], 1),
            'avg_entities_per_graph': self.stats['entities_extracted'] / max(self.stats['subgraphs_built'], 1),
            'avg_relations_per_graph': self.stats['relations_extracted'] / max(self.stats['subgraphs_built'], 1)
        }