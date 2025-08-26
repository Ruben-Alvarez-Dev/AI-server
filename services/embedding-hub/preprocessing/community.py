"""
Community Detection Preprocessor
Specialized preprocessing for graph clustering and community detection in LazyGraphRAG
Optimized for node relationships and community boundary identification
"""

import re
import logging
from typing import Dict, Any, List, Union, Set, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict

logger = logging.getLogger("embedding-hub.community")

@dataclass
class CommunityContext:
    """Context information for community detection processing"""
    entity_mentions: List[str]
    relationships: List[Tuple[str, str, str]]  # (entity1, relation, entity2)
    topics: List[str]
    semantic_clusters: List[List[str]]
    connectivity_score: float
    centrality_indicators: Dict[str, float]
    community_markers: List[str]

class CommunityPreprocessor:
    """
    Preprocessor specialized for community detection in graph structures
    
    Key principles:
    1. Extract entity mentions and relationships for node identification
    2. Identify semantic clusters and topic boundaries
    3. Optimize embeddings for clustering algorithms
    4. Preserve relationship strength indicators
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.extract_entity_mentions = self.preprocessing_options.get('extract_entity_mentions', True)
        self.relationship_detection = self.preprocessing_options.get('relationship_detection', True)
        self.clustering_optimization = self.preprocessing_options.get('clustering_optimization', True)
        self.community_boundary_sensitivity = self.preprocessing_options.get('community_boundary_sensitivity', 'high')
        
        # Entity patterns for different types
        self.entity_patterns = {
            'person': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # John Smith
            'organization': r'\b[A-Z][a-z]*\s*(?:Inc|Corp|LLC|Ltd|Company|Organization|University|Institute)\b',
            'technology': r'\b[A-Z]{2,}\b|[A-Z][a-z]+(?:[A-Z][a-z]*)+\b',  # API, JavaScript, React
            'concept': r'\b(?:concept|principle|method|approach|technique|algorithm|strategy)\s+of\s+\w+\b',
            'location': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:City|State|Country|Avenue|Street|Road))\b'
        }
        
        # Relationship indicators
        self.relationship_patterns = {
            'is_a': [r'\bis\s+a\b', r'\bare\s+a\b', r'\btype\s+of\b', r'\bkind\s+of\b'],
            'part_of': [r'\bpart\s+of\b', r'\bcomponent\s+of\b', r'\bmember\s+of\b', r'\belement\s+of\b'],
            'uses': [r'\buses\b', r'\bemploys\b', r'\butilizes\b', r'\bapplies\b', r'\bimplements\b'],
            'related_to': [r'\brelated\s+to\b', r'\bassociated\s+with\b', r'\bconnected\s+to\b', r'\blinked\s+to\b'],
            'similar_to': [r'\bsimilar\s+to\b', r'\blike\b', r'\bresembles\b', r'\bcompared\s+to\b'],
            'depends_on': [r'\bdepends\s+on\b', r'\brequires\b', r'\bneeds\b', r'\brelies\s+on\b'],
            'created_by': [r'\bcreated\s+by\b', r'\bdeveloped\s+by\b', r'\bmade\s+by\b', r'\bbuilt\s+by\b'],
            'contains': [r'\bcontains\b', r'\bincludes\b', r'\bhas\b', r'\bconsists\s+of\b']
        }
        
        # Topic indicators for clustering
        self.topic_patterns = {
            'technical': r'(?i)\b(?:programming|development|software|system|architecture|database|api|framework)\b',
            'business': r'(?i)\b(?:business|market|strategy|management|revenue|customer|client|company)\b',
            'research': r'(?i)\b(?:research|study|analysis|experiment|methodology|hypothesis|findings)\b',
            'education': r'(?i)\b(?:education|learning|teaching|curriculum|course|training|tutorial)\b',
            'health': r'(?i)\b(?:health|medical|healthcare|treatment|diagnosis|patient|clinical)\b',
            'finance': r'(?i)\b(?:finance|financial|money|investment|banking|economics|cost)\b'
        }
        
        logger.info(f"Initialized Community Detection preprocessor with sensitivity: {self.community_boundary_sensitivity}")
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess content for community detection and graph clustering
        
        Args:
            content: Raw content for community analysis
            metadata: Additional context information
            
        Returns:
            Preprocessed content optimized for community detection
        """
        try:
            # Convert to string if needed
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Analyze community structure
            context = self._analyze_community_structure(content)
            
            # Apply preprocessing steps
            processed_content = content
            
            if self.extract_entity_mentions:
                processed_content = self._enhance_entity_mentions(processed_content, context)
            
            if self.relationship_detection:
                processed_content = self._highlight_relationships(processed_content, context)
            
            if self.clustering_optimization:
                processed_content = self._optimize_for_clustering(processed_content, context)
            
            # Add community context for embeddings
            processed_content = self._add_community_context(processed_content, context, metadata)
            
            logger.debug(f"Community preprocessing completed - Entities: {len(context.entity_mentions)}, Relations: {len(context.relationships)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error in community preprocessing: {e}")
            return content  # Fallback to original content
    
    def _analyze_community_structure(self, content: str) -> CommunityContext:
        """Analyze content structure for community detection patterns"""
        
        # Extract entity mentions
        entity_mentions = self._extract_entity_mentions(content)
        
        # Detect relationships between entities
        relationships = self._detect_relationships(content, entity_mentions)
        
        # Identify topics for semantic clustering
        topics = self._identify_topics(content)
        
        # Create semantic clusters
        semantic_clusters = self._create_semantic_clusters(content, entity_mentions)
        
        # Calculate connectivity score
        connectivity_score = self._calculate_connectivity(entity_mentions, relationships)
        
        # Identify centrality indicators
        centrality_indicators = self._identify_centrality_indicators(content, entity_mentions)
        
        # Extract community markers
        community_markers = self._extract_community_markers(content)
        
        return CommunityContext(
            entity_mentions=entity_mentions,
            relationships=relationships,
            topics=topics,
            semantic_clusters=semantic_clusters,
            connectivity_score=connectivity_score,
            centrality_indicators=centrality_indicators,
            community_markers=community_markers
        )
    
    def _extract_entity_mentions(self, content: str) -> List[str]:
        """Extract entity mentions for node identification"""
        
        entities = []
        
        # Extract using predefined patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, content)
            entities.extend([(match, entity_type) for match in matches])
        
        # Extract capitalized terms (potential entities)
        capitalized_terms = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', content)
        entities.extend([(term, 'general') for term in capitalized_terms])
        
        # Extract quoted terms (often important concepts)
        quoted_terms = re.findall(r'"([^"]+)"', content)
        quoted_terms.extend(re.findall(r"'([^']+)'", content))
        entities.extend([(term, 'concept') for term in quoted_terms if len(term) > 2])
        
        # Extract technical terms and acronyms
        technical_terms = re.findall(r'\b[A-Z]{2,}\b|\b\w*[A-Z]\w*[A-Z]\w*\b', content)
        entities.extend([(term, 'technical') for term in technical_terms])
        
        # Remove duplicates and filter by length
        unique_entities = list(set([entity for entity, _ in entities if len(entity) > 2]))
        
        return unique_entities[:20]  # Limit to top 20 entities
    
    def _detect_relationships(self, content: str, entities: List[str]) -> List[Tuple[str, str, str]]:
        """Detect relationships between entities"""
        
        relationships = []
        
        # Create entity mention index
        entity_positions = {}
        for entity in entities:
            positions = []
            start = 0
            while True:
                pos = content.find(entity, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            entity_positions[entity] = positions
        
        # Look for relationships between nearby entities
        for relation_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    match_pos = match.start()
                    
                    # Find entities near this relationship indicator
                    nearby_entities = []
                    for entity in entities:
                        for pos in entity_positions.get(entity, []):
                            if abs(pos - match_pos) < 100:  # Within 100 characters
                                nearby_entities.append((entity, pos))
                    
                    # Create relationships between nearby entities
                    nearby_entities.sort(key=lambda x: x[1])  # Sort by position
                    for i in range(len(nearby_entities) - 1):
                        entity1 = nearby_entities[i][0]
                        entity2 = nearby_entities[i + 1][0]
                        if entity1 != entity2:
                            relationships.append((entity1, relation_type, entity2))
        
        return list(set(relationships))[:15]  # Limit and remove duplicates
    
    def _identify_topics(self, content: str) -> List[str]:
        """Identify main topics for semantic clustering"""
        
        topics = []
        content_lower = content.lower()
        
        # Use topic patterns to identify domains
        for topic, pattern in self.topic_patterns.items():
            matches = len(re.findall(pattern, content))
            if matches > 0:
                topics.append((topic, matches))
        
        # Sort by frequency and return top topics
        topics.sort(key=lambda x: x[1], reverse=True)
        
        return [topic for topic, _ in topics[:5]]
    
    def _create_semantic_clusters(self, content: str, entities: List[str]) -> List[List[str]]:
        """Create semantic clusters of related entities"""
        
        clusters = []
        
        # Group entities by co-occurrence patterns
        entity_cooccurrence = defaultdict(list)
        
        # Split content into sentences for local context analysis
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence_entities = [entity for entity in entities if entity in sentence]
            
            if len(sentence_entities) > 1:
                # All entities in this sentence are related
                for i, entity1 in enumerate(sentence_entities):
                    for entity2 in sentence_entities[i+1:]:
                        entity_cooccurrence[entity1].append(entity2)
                        entity_cooccurrence[entity2].append(entity1)
        
        # Create clusters from co-occurrence data
        processed_entities = set()
        
        for entity, related_entities in entity_cooccurrence.items():
            if entity not in processed_entities:
                cluster = [entity]
                cluster_entities = Counter(related_entities)
                
                # Add highly co-occurring entities to cluster
                for related_entity, count in cluster_entities.most_common(3):
                    if count > 1 and related_entity not in processed_entities:
                        cluster.append(related_entity)
                        processed_entities.add(related_entity)
                
                if len(cluster) > 1:
                    clusters.append(cluster)
                    for e in cluster:
                        processed_entities.add(e)
        
        return clusters
    
    def _calculate_connectivity(self, entities: List[str], relationships: List[Tuple[str, str, str]]) -> float:
        """Calculate connectivity score for the entity graph"""
        
        if not entities or not relationships:
            return 0.0
        
        # Count unique entity pairs in relationships
        entity_pairs = set()
        for entity1, _, entity2 in relationships:
            if entity1 in entities and entity2 in entities:
                pair = tuple(sorted([entity1, entity2]))
                entity_pairs.add(pair)
        
        # Calculate connectivity as ratio of actual connections to possible connections
        max_possible_connections = len(entities) * (len(entities) - 1) // 2
        actual_connections = len(entity_pairs)
        
        if max_possible_connections == 0:
            return 0.0
        
        connectivity = actual_connections / max_possible_connections
        return min(connectivity, 1.0)
    
    def _identify_centrality_indicators(self, content: str, entities: List[str]) -> Dict[str, float]:
        """Identify centrality indicators for entities"""
        
        centrality_scores = {}
        
        for entity in entities:
            score = 0.0
            
            # Frequency-based centrality
            frequency = content.lower().count(entity.lower())
            score += min(frequency / 10, 2.0)  # Normalize frequency contribution
            
            # Position-based centrality (earlier mentions are more central)
            first_mention = content.find(entity)
            if first_mention != -1:
                position_score = 1.0 - (first_mention / len(content))
                score += position_score
            
            # Context-based centrality (mentioned in important contexts)
            important_contexts = ['abstract', 'introduction', 'conclusion', 'summary', 'key', 'important', 'main']
            for context in important_contexts:
                if re.search(rf'\b{context}\b.*?\b{re.escape(entity)}\b', content, re.IGNORECASE):
                    score += 0.5
            
            centrality_scores[entity] = score
        
        return centrality_scores
    
    def _extract_community_markers(self, content: str) -> List[str]:
        """Extract markers that indicate community boundaries"""
        
        markers = []
        
        # Section markers
        section_markers = re.findall(r'(?i)\b(?:section|chapter|part|topic|category|group|cluster)\s+\w+', content)
        markers.extend(section_markers)
        
        # Transition markers
        transition_markers = re.findall(r'(?i)\b(?:however|moreover|furthermore|in contrast|on the other hand|similarly)\b', content)
        markers.extend(transition_markers)
        
        # Boundary indicators
        boundary_indicators = re.findall(r'(?i)\b(?:separate|distinct|different|unique|specific|particular)\b', content)
        markers.extend(boundary_indicators)
        
        return list(set(markers))
    
    def _enhance_entity_mentions(self, content: str, context: CommunityContext) -> str:
        """Enhance entity mentions with community markers"""
        
        enhanced_content = content
        
        # Add entity type markers
        for entity in context.entity_mentions:
            if entity in enhanced_content:
                enhanced_content = enhanced_content.replace(
                    entity,
                    f"[ENTITY:{entity}]",
                    1  # Only replace first occurrence to avoid over-marking
                )
        
        return enhanced_content
    
    def _highlight_relationships(self, content: str, context: CommunityContext) -> str:
        """Highlight detected relationships"""
        
        if not context.relationships:
            return content
        
        # Add relationship section
        relationship_section = ["[RELATIONSHIPS]"]
        
        for entity1, relation, entity2 in context.relationships:
            relationship_section.append(f"{entity1} --{relation}-> {entity2}")
        
        relationship_section.append("[/RELATIONSHIPS]")
        
        return content + "\n" + "\n".join(relationship_section)
    
    def _optimize_for_clustering(self, content: str, context: CommunityContext) -> str:
        """Optimize content for clustering algorithms"""
        
        # Add clustering hints based on semantic clusters
        if context.semantic_clusters:
            clustering_section = ["[CLUSTERING_HINTS]"]
            
            for i, cluster in enumerate(context.semantic_clusters):
                clustering_section.append(f"Cluster_{i}: {', '.join(cluster)}")
            
            clustering_section.append("[/CLUSTERING_HINTS]")
            
            content = content + "\n" + "\n".join(clustering_section)
        
        # Add topic boundaries
        if context.topics:
            topic_section = f"[TOPIC_DOMAINS: {', '.join(context.topics)}]"
            content = content + "\n" + topic_section
        
        return content
    
    def _add_community_context(self, content: str, context: CommunityContext, metadata: Dict[str, Any]) -> str:
        """Add comprehensive community context for embeddings"""
        
        # Create context header
        context_header = [
            "[COMMUNITY_CONTEXT]",
            f"Entity_Count: {len(context.entity_mentions)}",
            f"Relationship_Count: {len(context.relationships)}",
            f"Topic_Count: {len(context.topics)}",
            f"Semantic_Clusters: {len(context.semantic_clusters)}",
            f"Connectivity_Score: {context.connectivity_score:.3f}"
        ]
        
        # Add top entities by centrality
        if context.centrality_indicators:
            top_entities = sorted(context.centrality_indicators.items(), key=lambda x: x[1], reverse=True)[:3]
            central_entities = [entity for entity, _ in top_entities]
            context_header.append(f"Central_Entities: {', '.join(central_entities)}")
        
        # Add topic information
        if context.topics:
            context_header.append(f"Primary_Topics: {', '.join(context.topics[:3])}")
        
        # Add clustering information
        if context.semantic_clusters:
            largest_cluster = max(context.semantic_clusters, key=len)
            context_header.append(f"Largest_Cluster_Size: {len(largest_cluster)}")
        
        # Add community markers
        if context.community_markers:
            context_header.append(f"Community_Markers: {len(context.community_markers)}")
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                if key in ['document_type', 'domain', 'community_context'] and isinstance(value, str):
                    context_header.append(f"{key}: {value}")
        
        context_header.append("[/COMMUNITY_CONTEXT]")
        
        # Combine context with content
        full_content = "\n".join(context_header) + "\n\n" + content
        
        return full_content
    
    def extract_community_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features for community detection algorithms
        """
        
        context = self._analyze_community_structure(content)
        
        features = {
            "graph_structure": {
                "node_count": len(context.entity_mentions),
                "edge_count": len(context.relationships),
                "connectivity_score": context.connectivity_score,
                "cluster_count": len(context.semantic_clusters)
            },
            "entities": {
                "entity_list": context.entity_mentions,
                "centrality_scores": context.centrality_indicators,
                "entity_types": self._classify_entities(context.entity_mentions, content)
            },
            "relationships": {
                "relationship_list": context.relationships,
                "relationship_types": list(set([rel for _, rel, _ in context.relationships])),
                "relationship_strength": self._calculate_relationship_strengths(context.relationships)
            },
            "clustering": {
                "semantic_clusters": context.semantic_clusters,
                "topic_domains": context.topics,
                "community_markers": context.community_markers,
                "boundary_indicators": len(context.community_markers)
            },
            "optimization": {
                "clustering_recommendation": self._recommend_clustering_algorithm(context),
                "community_detection_hints": self._generate_clustering_hints(context),
                "similarity_optimization": self._suggest_similarity_measures(context)
            }
        }
        
        return features
    
    def _classify_entities(self, entities: List[str], content: str) -> Dict[str, str]:
        """Classify entities by type"""
        
        entity_types = {}
        
        for entity in entities:
            entity_type = 'general'
            
            # Check against patterns
            for etype, pattern in self.entity_patterns.items():
                if re.search(re.escape(entity), content):
                    if re.search(pattern, entity):
                        entity_type = etype
                        break
            
            entity_types[entity] = entity_type
        
        return entity_types
    
    def _calculate_relationship_strengths(self, relationships: List[Tuple[str, str, str]]) -> Dict[Tuple[str, str], float]:
        """Calculate strength scores for relationships"""
        
        relationship_counts = Counter()
        for entity1, relation, entity2 in relationships:
            pair = tuple(sorted([entity1, entity2]))
            relationship_counts[pair] += 1
        
        # Convert counts to normalized strength scores
        max_count = max(relationship_counts.values()) if relationship_counts else 1
        
        strengths = {}
        for pair, count in relationship_counts.items():
            strengths[pair] = count / max_count
        
        return strengths
    
    def _recommend_clustering_algorithm(self, context: CommunityContext) -> str:
        """Recommend clustering algorithm based on context"""
        
        if context.connectivity_score > 0.7:
            return "hierarchical_clustering"
        elif len(context.semantic_clusters) > 3:
            return "k_means_clustering"
        elif context.connectivity_score < 0.3:
            return "density_based_clustering"
        else:
            return "spectral_clustering"
    
    def _generate_clustering_hints(self, context: CommunityContext) -> List[str]:
        """Generate hints for clustering algorithms"""
        
        hints = []
        
        if context.connectivity_score > 0.5:
            hints.append("high_connectivity")
        
        if len(context.topics) > 2:
            hints.append("multi_topic_content")
        
        if len(context.semantic_clusters) > 0:
            hints.append("semantic_structure_present")
        
        if context.centrality_indicators:
            max_centrality = max(context.centrality_indicators.values())
            if max_centrality > 2.0:
                hints.append("strong_central_entities")
        
        return hints
    
    def _suggest_similarity_measures(self, context: CommunityContext) -> List[str]:
        """Suggest similarity measures for community detection"""
        
        measures = ["cosine_similarity"]  # Default
        
        if len(context.relationships) > 5:
            measures.append("jaccard_similarity")
        
        if context.connectivity_score > 0.4:
            measures.append("graph_based_similarity")
        
        if len(context.topics) > 1:
            measures.append("topic_similarity")
        
        return measures