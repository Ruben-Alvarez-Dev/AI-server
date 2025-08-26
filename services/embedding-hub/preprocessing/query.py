"""
Query Preprocessor
Specialized preprocessing for search queries and retrieval operations
Optimized for semantic similarity and retrieval effectiveness
"""

import re
import logging
from typing import Dict, Any, List, Union, Set
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger("embedding-hub.query")

@dataclass
class QueryContext:
    """Context information for query processing"""
    query_type: str
    intent: str
    entities: List[str]
    keywords: List[str]
    question_words: List[str]
    domain: str
    complexity_score: float
    expanded_terms: List[str]

class QueryPreprocessor:
    """
    Preprocessor specialized for query and retrieval optimization
    
    Key principles:
    1. Identify search intent and query type
    2. Extract and expand key entities and concepts
    3. Optimize for semantic similarity matching
    4. Enhance retrieval effectiveness through context
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.query_expansion = self.preprocessing_options.get('query_expansion', True)
        self.intent_detection = self.preprocessing_options.get('intent_detection', True)
        self.entity_extraction = self.preprocessing_options.get('entity_extraction', True)
        self.synonym_expansion = self.preprocessing_options.get('synonym_expansion', False)
        self.stop_word_handling = self.preprocessing_options.get('stop_word_handling', 'contextual')
        
        # Query type patterns
        self.query_patterns = {
            'how_to': r'(?i)^how\s+(?:to|do|can|should)\s+(?:i\s+)?(.+)',
            'what_is': r'(?i)^what\s+(?:is|are|was|were)\s+(.+)',
            'why': r'(?i)^why\s+(?:is|are|do|does|did|would|should)\s*(.+)',
            'when': r'(?i)^when\s+(?:is|are|do|does|did|would|should)\s*(.+)',
            'where': r'(?i)^where\s+(?:is|are|do|does|can|should)\s*(.+)',
            'who': r'(?i)^who\s+(?:is|are|was|were|can|should)\s*(.+)',
            'which': r'(?i)^which\s+(.+)',
            'comparison': r'(?i)\b(?:vs|versus|compare|comparison|difference|better|best)\b',
            'definition': r'(?i)\b(?:define|definition|meaning|means|explain)\b',
            'example': r'(?i)\b(?:example|sample|instance|demo|demonstration)\b',
            'troubleshooting': r'(?i)\b(?:error|issue|problem|bug|fix|solve|troubleshoot)\b',
            'implementation': r'(?i)\b(?:implement|build|create|setup|install|configure)\b'
        }
        
        # Intent indicators
        self.intent_patterns = {
            'informational': [r'(?i)\b(?:what|why|how|explain|describe|definition)\b'],
            'navigational': [r'(?i)\b(?:find|locate|go to|navigate|page|site)\b'],
            'transactional': [r'(?i)\b(?:buy|purchase|download|install|signup|register)\b'],
            'instructional': [r'(?i)\b(?:how to|tutorial|guide|step|instructions)\b'],
            'comparative': [r'(?i)\b(?:vs|versus|compare|better|best|difference)\b'],
            'troubleshooting': [r'(?i)\b(?:error|issue|problem|fix|solve|debug)\b']
        }
        
        # Domain indicators
        self.domain_patterns = {
            'programming': [r'(?i)\b(?:code|coding|programming|software|developer|api|function|class|method|algorithm)\b'],
            'web_development': [r'(?i)\b(?:html|css|javascript|react|angular|vue|frontend|backend|web|website)\b'],
            'data_science': [r'(?i)\b(?:data|dataset|analysis|machine learning|ai|model|python|pandas|numpy)\b'],
            'system_admin': [r'(?i)\b(?:server|linux|windows|admin|configuration|network|database|deployment)\b'],
            'mobile_dev': [r'(?i)\b(?:mobile|ios|android|app|application|flutter|react native)\b'],
            'general_tech': [r'(?i)\b(?:technology|tech|computer|software|hardware|system)\b']
        }
        
        # Stop words for contextual handling
        self.stop_words = {
            'common': {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
                      'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
                      'to', 'was', 'will', 'with'},
            'query_specific': {'how', 'what', 'why', 'when', 'where', 'who', 'which', 'can', 
                              'do', 'does', 'did', 'would', 'should', 'could'}
        }
        
        logger.info(f"Initialized Query preprocessor with expansion: {self.query_expansion}")
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess query content for optimal retrieval
        
        Args:
            content: Raw query content
            metadata: Additional context information
            
        Returns:
            Preprocessed query optimized for semantic matching
        """
        try:
            # Convert to string if needed
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Clean and normalize query
            cleaned_query = self._clean_query(content)
            
            # Analyze query context
            context = self._analyze_query_structure(cleaned_query)
            
            # Apply preprocessing steps
            processed_query = cleaned_query
            
            if self.intent_detection:
                processed_query = self._enhance_intent_markers(processed_query, context)
            
            if self.entity_extraction:
                processed_query = self._highlight_entities(processed_query, context)
            
            if self.query_expansion:
                processed_query = self._expand_query_terms(processed_query, context)
            
            # Handle stop words based on configuration
            processed_query = self._handle_stop_words(processed_query, context)
            
            # Add query context for embeddings
            processed_query = self._add_query_context(processed_query, context, metadata)
            
            logger.debug(f"Query preprocessing completed - Type: {context.query_type}, Intent: {context.intent}")
            
            return processed_query
            
        except Exception as e:
            logger.error(f"Error in query preprocessing: {e}")
            return content  # Fallback to original content
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text"""
        
        # Remove extra whitespace
        cleaned = ' '.join(query.split())
        
        # Normalize punctuation
        cleaned = re.sub(r'[^\w\s\?\!\.,-]', '', cleaned)
        
        # Handle common query patterns
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _analyze_query_structure(self, query: str) -> QueryContext:
        """Analyze query structure and extract context information"""
        
        # Identify query type
        query_type = self._identify_query_type(query)
        
        # Detect intent
        intent = self._detect_intent(query)
        
        # Extract entities and keywords
        entities = self._extract_entities(query)
        keywords = self._extract_keywords(query)
        
        # Identify question words
        question_words = self._identify_question_words(query)
        
        # Determine domain
        domain = self._identify_domain(query)
        
        # Calculate complexity score
        complexity = self._calculate_query_complexity(query, entities, keywords)
        
        # Generate expanded terms
        expanded_terms = self._generate_expansions(query, entities, keywords)
        
        return QueryContext(
            query_type=query_type,
            intent=intent,
            entities=entities,
            keywords=keywords,
            question_words=question_words,
            domain=domain,
            complexity_score=complexity,
            expanded_terms=expanded_terms
        )
    
    def _identify_query_type(self, query: str) -> str:
        """Identify the type of query based on patterns"""
        
        query_lower = query.lower().strip()
        
        # Check specific patterns
        for query_type, pattern in self.query_patterns.items():
            if re.search(pattern, query):
                return query_type
        
        # Check for question structure
        if query.strip().endswith('?'):
            if query_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who', 'which')):
                return 'question'
            else:
                return 'yes_no_question'
        
        # Check for imperative (command-like)
        if query_lower.startswith(('show', 'find', 'get', 'list', 'display', 'search')):
            return 'command'
        
        return 'keyword_search'
    
    def _detect_intent(self, query: str) -> str:
        """Detect search intent from query"""
        
        query_lower = query.lower()
        
        # Score each intent based on pattern matches
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query))
                score += matches
            intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return 'informational'  # Default intent
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract key entities from query"""
        
        entities = []
        
        # Capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)
        entities.extend(capitalized)
        
        # Technical terms and acronyms
        technical_terms = re.findall(r'\b[A-Z]{2,}\b|\b\w*[A-Z]\w*[A-Z]\w*\b', query)
        entities.extend(technical_terms)
        
        # Version numbers and identifiers
        versions = re.findall(r'\b\d+(?:\.\d+)+\b|\bv\d+(?:\.\d+)*\b', query)
        entities.extend(versions)
        
        # File extensions and formats
        formats = re.findall(r'\b\w+\.\w+\b|\b\.?\w{2,4}(?:\s+file)?\b', query)
        entities.extend([f for f in formats if len(f) <= 10])  # Filter out long matches
        
        # Remove duplicates and return
        return list(set([entity.strip() for entity in entities if len(entity) > 1]))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        
        # Remove stop words and extract meaningful terms
        words = query.lower().split()
        
        # Filter stop words based on configuration
        if self.stop_word_handling == 'remove':
            filtered_words = [w for w in words if w not in self.stop_words['common']]
        elif self.stop_word_handling == 'contextual':
            # Keep question words but remove common stop words
            filtered_words = [w for w in words if w not in self.stop_words['common']]
        else:  # keep_all
            filtered_words = words
        
        # Extract meaningful keywords (longer than 2 chars, not pure numbers)
        keywords = [
            word for word in filtered_words 
            if len(word) > 2 and not word.isdigit() and word.isalpha()
        ]
        
        # Add technical terms and compound words
        compound_terms = re.findall(r'\b\w+[-_]\w+\b', query.lower())
        keywords.extend(compound_terms)
        
        return list(set(keywords[:10]))  # Limit to top 10 keywords
    
    def _identify_question_words(self, query: str) -> List[str]:
        """Identify question words in the query"""
        
        question_words = []
        query_lower = query.lower()
        
        wh_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose', 'whom']
        
        for word in wh_words:
            if word in query_lower:
                question_words.append(word)
        
        # Add modal questions
        modal_words = ['can', 'could', 'would', 'should', 'might', 'may', 'will', 'shall']
        for word in modal_words:
            if query_lower.startswith(word + ' '):
                question_words.append(word)
        
        return question_words
    
    def _identify_domain(self, query: str) -> str:
        """Identify the domain/topic of the query"""
        
        query_lower = query.lower()
        
        # Score each domain based on pattern matches
        domain_scores = {}
        
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query))
                score += matches
            domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'general'
    
    def _calculate_query_complexity(self, query: str, entities: List[str], keywords: List[str]) -> float:
        """Calculate query complexity score"""
        
        complexity_score = 0.0
        
        # Base complexity from length
        complexity_score += min(len(query.split()) / 10, 2.0)
        
        # Add complexity for entities and keywords
        complexity_score += len(entities) * 0.3
        complexity_score += len(keywords) * 0.2
        
        # Add complexity for question structure
        if query.strip().endswith('?'):
            complexity_score += 0.5
        
        # Add complexity for technical terms
        if any(len(entity) > 8 for entity in entities):
            complexity_score += 1.0
        
        # Add complexity for compound queries (multiple topics)
        if ' and ' in query.lower() or ' or ' in query.lower():
            complexity_score += 1.5
        
        return min(complexity_score, 10.0)
    
    def _generate_expansions(self, query: str, entities: List[str], keywords: List[str]) -> List[str]:
        """Generate query expansions for better matching"""
        
        expansions = []
        
        # Add synonyms for common programming terms
        programming_synonyms = {
            'function': ['method', 'procedure', 'routine'],
            'variable': ['var', 'parameter', 'field'],
            'class': ['object', 'type', 'component'],
            'error': ['exception', 'bug', 'issue', 'problem'],
            'install': ['setup', 'configure', 'deploy'],
            'create': ['build', 'generate', 'make'],
            'fix': ['solve', 'resolve', 'repair']
        }
        
        # Add expansions for keywords
        for keyword in keywords:
            if keyword in programming_synonyms:
                expansions.extend(programming_synonyms[keyword])
        
        # Add common variations
        for entity in entities:
            if entity.lower().endswith('js'):
                expansions.append(entity[:-2] + 'javascript')
            elif entity.lower() == 'js':
                expansions.append('javascript')
            elif entity.lower() == 'py':
                expansions.append('python')
        
        return list(set(expansions))
    
    def _enhance_intent_markers(self, query: str, context: QueryContext) -> str:
        """Add intent markers to enhance query understanding"""
        
        # Add intent marker at the beginning
        enhanced_query = f"[INTENT:{context.intent.upper()}] {query}"
        
        # Add query type information
        if context.query_type != 'keyword_search':
            enhanced_query = f"[TYPE:{context.query_type.upper()}] {enhanced_query}"
        
        return enhanced_query
    
    def _highlight_entities(self, query: str, context: QueryContext) -> str:
        """Highlight important entities in the query"""
        
        highlighted_query = query
        
        # Highlight entities
        for entity in context.entities:
            if entity in highlighted_query:
                highlighted_query = highlighted_query.replace(
                    entity, 
                    f"[ENTITY:{entity}]"
                )
        
        return highlighted_query
    
    def _expand_query_terms(self, query: str, context: QueryContext) -> str:
        """Expand query with additional terms"""
        
        if not context.expanded_terms:
            return query
        
        # Add expanded terms section
        expansion_section = f" [EXPANSIONS: {', '.join(context.expanded_terms[:5])}]"
        
        return query + expansion_section
    
    def _handle_stop_words(self, query: str, context: QueryContext) -> str:
        """Handle stop words based on configuration"""
        
        if self.stop_word_handling == 'keep_all':
            return query
        
        # For query processing, we generally want to keep question words
        # as they provide important context for retrieval
        return query
    
    def _add_query_context(self, query: str, context: QueryContext, metadata: Dict[str, Any]) -> str:
        """Add comprehensive query context for embeddings"""
        
        # Create context header
        context_header = [
            "[QUERY_CONTEXT]",
            f"Type: {context.query_type}",
            f"Intent: {context.intent}",
            f"Domain: {context.domain}",
            f"Complexity: {context.complexity_score:.2f}"
        ]
        
        # Add entity information
        if context.entities:
            context_header.append(f"Entities: {', '.join(context.entities[:5])}")
        
        # Add keyword information
        if context.keywords:
            context_header.append(f"Keywords: {', '.join(context.keywords[:5])}")
        
        # Add question words
        if context.question_words:
            context_header.append(f"Question_Words: {', '.join(context.question_words)}")
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                if key in ['user_context', 'search_context', 'previous_query'] and isinstance(value, str):
                    context_header.append(f"{key}: {value}")
        
        context_header.append("[/QUERY_CONTEXT]")
        
        # Combine context with query
        full_query = "\n".join(context_header) + "\n\n" + query
        
        return full_query
    
    def extract_query_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features from query for specialized processing
        """
        
        cleaned_query = self._clean_query(content)
        context = self._analyze_query_structure(cleaned_query)
        
        features = {
            "query_classification": {
                "type": context.query_type,
                "intent": context.intent,
                "domain": context.domain,
                "complexity_score": context.complexity_score
            },
            "linguistic_features": {
                "question_words": context.question_words,
                "word_count": len(cleaned_query.split()),
                "is_question": cleaned_query.strip().endswith('?'),
                "has_entities": len(context.entities) > 0
            },
            "semantic_elements": {
                "entities": context.entities[:10],
                "keywords": context.keywords[:10],
                "expanded_terms": context.expanded_terms[:10]
            },
            "retrieval_optimization": {
                "primary_keywords": context.keywords[:3],
                "search_terms": context.entities + context.keywords,
                "expansion_candidates": context.expanded_terms[:5]
            }
        }
        
        return features
    
    def optimize_for_retrieval(self, query: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Optimize query specifically for retrieval operations
        Returns multiple query variations for different matching strategies
        """
        
        context = self._analyze_query_structure(query)
        
        optimization_result = {
            "original_query": query,
            "optimized_variations": {
                "semantic": self._create_semantic_query(query, context),
                "keyword": self._create_keyword_query(query, context),
                "entity_focused": self._create_entity_focused_query(query, context),
                "expanded": self._create_expanded_query(query, context)
            },
            "retrieval_hints": {
                "primary_terms": context.keywords[:3],
                "important_entities": context.entities[:3],
                "domain_context": context.domain,
                "intent_context": context.intent
            },
            "matching_strategy": self._suggest_matching_strategy(context)
        }
        
        return optimization_result
    
    def _create_semantic_query(self, query: str, context: QueryContext) -> str:
        """Create semantically optimized query"""
        return f"{query} {' '.join(context.expanded_terms[:3])}"
    
    def _create_keyword_query(self, query: str, context: QueryContext) -> str:
        """Create keyword-focused query"""
        return " ".join(context.keywords + context.entities)
    
    def _create_entity_focused_query(self, query: str, context: QueryContext) -> str:
        """Create entity-focused query"""
        if context.entities:
            return f"{' '.join(context.entities)} {query}"
        return query
    
    def _create_expanded_query(self, query: str, context: QueryContext) -> str:
        """Create expanded query with all relevant terms"""
        all_terms = context.keywords + context.entities + context.expanded_terms
        unique_terms = list(set(all_terms))[:8]  # Limit to avoid over-expansion
        return f"{query} {' '.join(unique_terms)}"
    
    def _suggest_matching_strategy(self, context: QueryContext) -> str:
        """Suggest optimal matching strategy for the query"""
        
        if context.query_type in ['how_to', 'implementation']:
            return "procedural_matching"
        elif context.intent == 'comparative':
            return "comparative_matching"
        elif len(context.entities) > 2:
            return "entity_matching"
        elif context.complexity_score > 5:
            return "semantic_matching"
        else:
            return "hybrid_matching"