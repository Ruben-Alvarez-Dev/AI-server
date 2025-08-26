"""
Query processor implementation for Memory-Server.
Analyzes, expands and optimizes user queries.
"""

import logging
import asyncio
import time
import re
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from ..generation import TextGenerator, GenerationRequest, GenerationMode
from .models import QueryRequest, QueryResponse, QueryProcessorConfig, QueryType, QueryIntent

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Query processor for analyzing and enhancing user queries."""
    
    def __init__(self, config: Optional[QueryProcessorConfig] = None, text_generator: Optional[TextGenerator] = None):
        self.config = config or QueryProcessorConfig()
        self.text_generator = text_generator
        self.nlp = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._nlp_loading = False
        self._nlp_loaded = False
        
        # Keyword patterns for different query types
        self.type_patterns = {
            QueryType.FACTUAL: ["what is", "define", "explain", "who is", "when did", "where is"],
            QueryType.PROCEDURAL: ["how to", "steps", "process", "procedure", "tutorial", "guide"],
            QueryType.CODE_SEARCH: ["function", "class", "method", "implementation", "code", "api"],
            QueryType.DOCUMENT_SEARCH: ["document", "file", "report", "paper", "article"],
            QueryType.CONCEPTUAL: ["concept", "theory", "principle", "approach", "philosophy"],
            QueryType.CONVERSATIONAL: ["please", "can you", "could you", "help me", "i need"]
        }
        
        self.intent_patterns = {
            QueryIntent.SEARCH: ["find", "search", "look for", "locate", "show me"],
            QueryIntent.SUMMARIZE: ["summarize", "summary", "overview", "brief"],
            QueryIntent.EXPLAIN: ["explain", "clarify", "describe", "tell me about"],
            QueryIntent.COMPARE: ["compare", "difference", "versus", "vs", "contrast"],
            QueryIntent.GENERATE: ["create", "generate", "make", "build", "write"],
            QueryIntent.DEBUG: ["error", "bug", "issue", "problem", "debug", "fix"]
        }
    
    async def initialize(self):
        """Initialize NLP model if available."""
        if self._nlp_loaded or not SPACY_AVAILABLE:
            return
            
        if self._nlp_loading:
            # Wait for NLP to load if another request is loading it
            while self._nlp_loading:
                await asyncio.sleep(0.1)
            return
        
        try:
            self._nlp_loading = True
            logger.info("Loading spaCy NLP model")
            
            # Try to load spaCy model in thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._load_nlp_model
            )
            
            self._nlp_loaded = True
            logger.info("spaCy NLP model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}. Using fallback processing.")
            self._nlp_loaded = False
        finally:
            self._nlp_loading = False
    
    def _load_nlp_model(self):
        """Load spaCy model synchronously."""
        try:
            # Try common English models
            model_names = ["en_core_web_sm", "en_core_web_md", "en_core_web_lg"]
            
            for model_name in model_names:
                try:
                    self.nlp = spacy.load(model_name)
                    logger.info(f"Loaded spaCy model: {model_name}")
                    break
                except OSError:
                    continue
            
            if not self.nlp:
                logger.warning("No spaCy model found. Install with: python -m spacy download en_core_web_sm")
                
        except Exception as e:
            logger.error(f"Error loading spaCy model: {e}")
            raise
    
    async def process(self, request: QueryRequest) -> QueryResponse:
        """
        Process and enhance user query.
        
        Args:
            request: Query processing request
            
        Returns:
            Processed query with metadata
        """
        start_time = time.time()
        
        try:
            # Initialize NLP if available
            await self.initialize()
            
            # Detect query type and intent
            query_type = self._detect_query_type(request.query)
            intent = self._detect_intent(request.query)
            
            # Extract keywords and entities
            keywords = await self._extract_keywords(request.query)
            entities = await self._extract_entities(request.query)
            
            # Expand query terms
            expanded_terms = []
            if self.config.enable_expansion:
                expanded_terms = await self._expand_query(request.query, query_type)
            
            # Process/enhance the query
            processed_query = await self._enhance_query(request, query_type, intent)
            
            # Calculate confidence
            confidence = self._calculate_confidence(request.query, keywords, entities)
            
            processing_time = time.time() - start_time
            
            return QueryResponse(
                original_query=request.query,
                processed_query=processed_query,
                query_type=query_type,
                intent=intent,
                keywords=keywords,
                entities=entities,
                expanded_terms=expanded_terms[:self.config.max_expanded_terms],
                confidence=confidence,
                processing_time=processing_time,
                metadata=request.metadata
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return self._fallback_response(request, time.time() - start_time)
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query."""
        query_lower = query.lower()
        
        # Score each type based on keyword matches
        type_scores = {}
        for query_type, patterns in self.type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            type_scores[query_type] = score
        
        # Return type with highest score, default to conversational
        best_type = max(type_scores, key=type_scores.get, default=QueryType.CONVERSATIONAL)
        
        # If no clear winner, use additional heuristics
        if type_scores[best_type] == 0:
            if "?" in query:
                return QueryType.FACTUAL
            elif re.search(r'\b(function|class|def|import)\b', query):
                return QueryType.CODE_SEARCH
            else:
                return QueryType.CONVERSATIONAL
        
        return best_type
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the intent of the query."""
        query_lower = query.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            intent_scores[intent] = score
        
        # Return intent with highest score, default to search
        best_intent = max(intent_scores, key=intent_scores.get, default=QueryIntent.SEARCH)
        
        if intent_scores[best_intent] == 0:
            return QueryIntent.SEARCH
        
        return best_intent
    
    async def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        if self.nlp:
            # Use spaCy for advanced keyword extraction
            return await self._extract_keywords_nlp(query)
        else:
            # Fallback to simple extraction
            return self._extract_keywords_simple(query)
    
    async def _extract_keywords_nlp(self, query: str) -> List[str]:
        """Extract keywords using spaCy."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_keywords_nlp_sync,
            query
        )
    
    def _extract_keywords_nlp_sync(self, query: str) -> List[str]:
        """Extract keywords using spaCy synchronously."""
        doc = self.nlp(query)
        keywords = []
        
        for token in doc:
            # Skip stop words, punctuation, and short tokens
            if (not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2 and
                token.pos_ in ['NOUN', 'VERB', 'ADJ', 'PROPN']):
                keywords.append(token.lemma_.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    def _extract_keywords_simple(self, query: str) -> List[str]:
        """Simple keyword extraction fallback."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    async def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query."""
        if self.nlp:
            # Use spaCy for entity extraction
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._extract_entities_nlp_sync,
                query
            )
        else:
            # Fallback to simple pattern matching
            return self._extract_entities_simple(query)
    
    def _extract_entities_nlp_sync(self, query: str) -> List[str]:
        """Extract entities using spaCy synchronously."""
        doc = self.nlp(query)
        entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'TECHNOLOGY']]
        return list(set(entities))  # Remove duplicates
    
    def _extract_entities_simple(self, query: str) -> List[str]:
        """Simple entity extraction fallback."""
        # Look for capitalized words (potential proper nouns)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        return list(set(entities))
    
    async def _expand_query(self, query: str, query_type: QueryType) -> List[str]:
        """Expand query with related terms."""
        if not self.text_generator or not self.config.use_llm_processing:
            return self._expand_query_simple(query)
        
        try:
            # Use LLM for query expansion
            expansion_request = GenerationRequest(
                query=f"Generate related search terms for: {query}",
                mode=GenerationMode.QUERY_EXPANSION,
                max_tokens=100,
                temperature=0.3
            )
            
            response = await self.text_generator.generate(expansion_request)
            
            # Parse expanded terms from response
            expanded_terms = self._parse_expanded_terms(response.answer)
            return expanded_terms
            
        except Exception as e:
            logger.warning(f"LLM query expansion failed: {e}. Using simple expansion.")
            return self._expand_query_simple(query)
    
    def _expand_query_simple(self, query: str) -> List[str]:
        """Simple query expansion with synonyms."""
        # Basic synonym dictionary for common terms
        synonyms = {
            'function': ['method', 'procedure', 'routine'],
            'error': ['bug', 'issue', 'problem', 'exception'],
            'create': ['make', 'build', 'generate', 'construct'],
            'find': ['search', 'locate', 'discover'],
            'implement': ['code', 'develop', 'build'],
            'document': ['file', 'paper', 'article', 'text']
        }
        
        expanded = []
        words = query.lower().split()
        
        for word in words:
            if word in synonyms:
                expanded.extend(synonyms[word])
        
        return list(set(expanded))  # Remove duplicates
    
    def _parse_expanded_terms(self, response: str) -> List[str]:
        """Parse expanded terms from LLM response."""
        # Simple parsing - look for comma-separated terms or bullet points
        terms = []
        
        # Split by common separators
        for separator in [',', '\n', '•', '-', '*']:
            if separator in response:
                parts = response.split(separator)
                for part in parts:
                    term = part.strip().strip('"\'').lower()
                    if term and len(term) > 2:
                        terms.append(term)
        
        # If no separators found, try to extract individual words
        if not terms:
            words = re.findall(r'\b\w+\b', response.lower())
            terms = [word for word in words if len(word) > 2]
        
        return list(set(terms))[:self.config.max_expanded_terms]
    
    async def _enhance_query(self, request: QueryRequest, query_type: QueryType, intent: QueryIntent) -> str:
        """Enhance the original query."""
        query = request.query
        
        # Add context-specific enhancements
        if request.workspace:
            query = f"[workspace:{request.workspace}] {query}"
        
        # Add type-specific enhancements
        if query_type == QueryType.CODE_SEARCH:
            if not any(term in query.lower() for term in ['function', 'class', 'method', 'implementation']):
                query = f"code implementation {query}"
        
        elif query_type == QueryType.PROCEDURAL:
            if not query.lower().startswith('how'):
                query = f"how to {query}"
        
        return query.strip()
    
    def _calculate_confidence(self, query: str, keywords: List[str], entities: List[str]) -> float:
        """Calculate processing confidence."""
        base_confidence = 0.5
        
        # More keywords/entities = higher confidence
        if len(keywords) > 3:
            base_confidence += 0.2
        if len(entities) > 0:
            base_confidence += 0.1
        
        # Clear question format = higher confidence
        if query.endswith('?'):
            base_confidence += 0.1
        
        # Length consideration
        if len(query.split()) > 5:
            base_confidence += 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    def _fallback_response(self, request: QueryRequest, processing_time: float) -> QueryResponse:
        """Fallback response when processing fails."""
        keywords = self._extract_keywords_simple(request.query)
        
        return QueryResponse(
            original_query=request.query,
            processed_query=request.query,
            query_type=QueryType.CONVERSATIONAL,
            intent=QueryIntent.SEARCH,
            keywords=keywords,
            entities=[],
            expanded_terms=[],
            confidence=0.3,
            processing_time=processing_time,
            metadata=request.metadata
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check processor health status."""
        status = {
            "status": "healthy",
            "nlp_loaded": self._nlp_loaded,
            "spacy_available": SPACY_AVAILABLE,
            "llm_processing": self.config.use_llm_processing and self.text_generator is not None
        }
        
        # Quick test
        try:
            test_request = QueryRequest(query="What is machine learning?")
            response = await self.process(test_request)
            status["last_test"] = "passed"
            status["last_test_confidence"] = response.confidence
        except Exception as e:
            status["status"] = "unhealthy"
            status["last_test"] = f"failed: {str(e)}"
        
        return status
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.nlp = None
        self._nlp_loaded = False