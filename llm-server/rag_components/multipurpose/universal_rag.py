"""
Universal RAG Engine - Multi-Purpose Document Intelligence
Supports development docs + personal documents + mixed knowledge domains
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document type classification"""
    CODE = "code"
    TECHNICAL_DOC = "technical_doc"
    PERSONAL_NOTE = "personal_note"
    RESEARCH_PAPER = "research_paper"
    BUSINESS_DOC = "business_doc"
    CREATIVE_WRITING = "creative_writing"
    REFERENCE = "reference"
    MIXED = "mixed"

class KnowledgeDomain(Enum):
    """Knowledge domain classification"""
    SOFTWARE_DEVELOPMENT = "software_development"
    AI_MACHINE_LEARNING = "ai_ml"
    BUSINESS_STRATEGY = "business_strategy"
    PERSONAL_KNOWLEDGE = "personal_knowledge"
    RESEARCH_ACADEMIC = "research_academic"
    CREATIVE_PROJECTS = "creative_projects"
    TECHNICAL_REFERENCE = "technical_reference"
    GENERAL_KNOWLEDGE = "general_knowledge"

@dataclass
class UniversalDocument:
    """Enhanced document with multi-domain metadata"""
    content: str
    doc_id: str
    title: str
    source_path: str
    doc_type: DocumentType
    knowledge_domains: List[KnowledgeDomain]
    
    # Enhanced metadata
    creation_time: float
    last_modified: float
    importance_score: float = 0.5
    access_frequency: int = 0
    
    # Content analysis
    language: str = "en"
    complexity_score: float = 0.5
    readability_score: float = 0.5
    
    # Relationships
    related_documents: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Context vectors (for different purposes)
    embeddings: Dict[str, List[float]] = field(default_factory=dict)
    
    # Usage patterns
    usage_contexts: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.5

@dataclass
class SearchContext:
    """Search context for different use cases"""
    query: str
    intent: str  # "development", "research", "creative", "reference", etc.
    domains: List[KnowledgeDomain]
    doc_types: List[DocumentType] = field(default_factory=list)
    time_relevance: Optional[str] = None  # "recent", "historical", "any"
    complexity_preference: Optional[str] = None  # "simple", "advanced", "any"

class UniversalRAG:
    """
    Universal RAG Engine for Multi-Purpose Document Intelligence
    
    Features:
    - Automatic document type classification
    - Domain-aware retrieval
    - Context-sensitive embedding selection
    - Personal knowledge integration
    - Development-aware search
    - Unlimited scalability (M1 Ultra optimized)
    """
    
    def __init__(
        self,
        storage_path: str = "./universal_knowledge",
        max_memory_gb: int = 50,  # Dedicated RAM for this system
        enable_gpu: bool = True
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.enable_gpu = enable_gpu
        
        # Document storage
        self.documents: Dict[str, UniversalDocument] = {}
        self.domain_indexes: Dict[KnowledgeDomain, Set[str]] = {
            domain: set() for domain in KnowledgeDomain
        }
        self.type_indexes: Dict[DocumentType, Set[str]] = {
            doc_type: set() for doc_type in DocumentType
        }
        
        # Multiple vector stores for different purposes
        self.vector_stores = {}  # domain -> vector_store
        self.embedding_engines = {}  # embedding_type -> engine
        
        # Analytics and optimization
        self.search_analytics = {
            'total_searches': 0,
            'domain_usage': {domain.value: 0 for domain in KnowledgeDomain},
            'type_usage': {doc_type.value: 0 for doc_type in DocumentType},
            'avg_response_time': 0.0
        }
        
        # Dynamic memory management
        self.memory_usage = 0
        self.last_cleanup = time.time()
        
        logger.info(f"UniversalRAG initialized: {max_memory_gb}GB RAM budget, GPU={enable_gpu}")
    
    async def ingest_document(
        self,
        content: str,
        title: str,
        source_path: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Intelligently ingest and classify documents
        """
        doc_id = hashlib.md5(f"{source_path}{title}{content[:100]}".encode()).hexdigest()
        
        logger.info(f"Ingesting document: {title}")
        
        # Automatic classification
        doc_type = await self._classify_document_type(content, title, source_path)
        knowledge_domains = await self._identify_knowledge_domains(content, title, metadata)
        
        # Content analysis
        analysis = await self._analyze_content(content)
        
        # Create universal document
        document = UniversalDocument(
            content=content,
            doc_id=doc_id,
            title=title,
            source_path=source_path,
            doc_type=doc_type,
            knowledge_domains=knowledge_domains,
            creation_time=time.time(),
            last_modified=time.time(),
            importance_score=analysis['importance'],
            language=analysis['language'],
            complexity_score=analysis['complexity'],
            readability_score=analysis['readability'],
            tags=metadata.get('tags', []) if metadata else []
        )
        
        # Generate embeddings for different contexts
        await self._generate_multi_context_embeddings(document)
        
        # Store document
        self.documents[doc_id] = document
        
        # Update indexes
        for domain in knowledge_domains:
            self.domain_indexes[domain].add(doc_id)
        self.type_indexes[doc_type].add(doc_id)
        
        # Update vector stores
        await self._update_vector_stores(document)
        
        logger.info(f"Document ingested: {doc_id[:8]}... ({doc_type.value}, domains: {[d.value for d in knowledge_domains]})")
        
        return doc_id
    
    async def intelligent_search(
        self,
        context: SearchContext,
        max_results: int = 20,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Context-aware intelligent search across all knowledge domains
        """
        start_time = time.time()
        self.search_analytics['total_searches'] += 1
        
        logger.info(f"Intelligent search: '{context.query}' (intent: {context.intent})")
        
        # Domain-specific search strategy
        search_results = []
        
        if context.intent == "development":
            search_results = await self._development_focused_search(context, max_results)
        elif context.intent == "research":
            search_results = await self._research_focused_search(context, max_results)
        elif context.intent == "creative":
            search_results = await self._creative_focused_search(context, max_results)
        elif context.intent == "personal":
            search_results = await self._personal_knowledge_search(context, max_results)
        else:
            # General cross-domain search
            search_results = await self._cross_domain_search(context, max_results)
        
        # Filter by score threshold
        filtered_results = [r for r in search_results if r['score'] >= score_threshold]
        
        # Update analytics
        for domain in context.domains:
            self.search_analytics['domain_usage'][domain.value] += 1
        
        response_time = time.time() - start_time
        self.search_analytics['avg_response_time'] = (
            (self.search_analytics['avg_response_time'] * (self.search_analytics['total_searches'] - 1) + response_time)
            / self.search_analytics['total_searches']
        )
        
        logger.info(f"Search completed: {len(filtered_results)} results in {response_time:.2f}s")
        
        return filtered_results[:max_results]
    
    async def _development_focused_search(
        self,
        context: SearchContext,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search optimized for development queries"""
        
        # Prioritize code and technical documents
        priority_types = [DocumentType.CODE, DocumentType.TECHNICAL_DOC, DocumentType.REFERENCE]
        priority_domains = [KnowledgeDomain.SOFTWARE_DEVELOPMENT, KnowledgeDomain.AI_MACHINE_LEARNING]
        
        results = []
        
        # Search in development-specific vector stores
        for domain in priority_domains:
            if domain in self.vector_stores:
                domain_results = await self._search_vector_store(
                    self.vector_stores[domain],
                    context.query,
                    max_results // 2
                )
                results.extend(domain_results)
        
        # Enhance with code-specific matching
        code_results = await self._code_semantic_search(context.query, max_results // 2)
        results.extend(code_results)
        
        # Sort by relevance + recency for development
        return sorted(results, key=lambda x: (x['score'], -x.get('age_penalty', 0)), reverse=True)
    
    async def _personal_knowledge_search(
        self,
        context: SearchContext,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search optimized for personal knowledge and notes"""
        
        # Focus on personal documents and notes
        priority_types = [DocumentType.PERSONAL_NOTE, DocumentType.CREATIVE_WRITING]
        priority_domains = [KnowledgeDomain.PERSONAL_KNOWLEDGE, KnowledgeDomain.CREATIVE_PROJECTS]
        
        results = []
        
        # Semantic search in personal domain
        if KnowledgeDomain.PERSONAL_KNOWLEDGE in self.vector_stores:
            results = await self._search_vector_store(
                self.vector_stores[KnowledgeDomain.PERSONAL_KNOWLEDGE],
                context.query,
                max_results
            )
        
        # Add relationship-based expansion
        expanded_results = await self._expand_with_related_documents(results, max_results)
        
        return expanded_results
    
    async def _cross_domain_search(
        self,
        context: SearchContext,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """General cross-domain search with intelligent ranking"""
        
        all_results = []
        results_per_domain = max(1, max_results // len(context.domains))
        
        # Search across specified domains
        for domain in context.domains:
            if domain in self.vector_stores:
                domain_results = await self._search_vector_store(
                    self.vector_stores[domain],
                    context.query,
                    results_per_domain
                )
                
                # Tag with domain for ranking
                for result in domain_results:
                    result['source_domain'] = domain.value
                
                all_results.extend(domain_results)
        
        # Intelligent re-ranking based on query intent
        ranked_results = await self._intelligent_rerank(all_results, context)
        
        return ranked_results[:max_results]
    
    async def _classify_document_type(
        self,
        content: str,
        title: str,
        source_path: str
    ) -> DocumentType:
        """Automatically classify document type"""
        
        # File extension hints
        path_lower = source_path.lower()
        
        # Code files
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
        if any(path_lower.endswith(ext) for ext in code_extensions):
            return DocumentType.CODE
        
        # Documentation
        doc_extensions = ['.md', '.rst', '.txt', '.pdf']
        if any(path_lower.endswith(ext) for ext in doc_extensions):
            # Further classify based on content
            if any(keyword in content.lower() for keyword in ['api', 'function', 'class', 'method', 'installation']):
                return DocumentType.TECHNICAL_DOC
            elif any(keyword in content.lower() for keyword in ['note:', 'todo:', 'remember', 'personal']):
                return DocumentType.PERSONAL_NOTE
        
        # Research papers (heuristics)
        if any(keyword in title.lower() for keyword in ['survey', 'analysis', 'study', 'research', 'paper']):
            return DocumentType.RESEARCH_PAPER
        
        # Business documents
        if any(keyword in content.lower() for keyword in ['business', 'strategy', 'market', 'revenue', 'customer']):
            return DocumentType.BUSINESS_DOC
        
        # Creative writing
        if any(keyword in content.lower() for keyword in ['story', 'poem', 'creative', 'fiction', 'narrative']):
            return DocumentType.CREATIVE_WRITING
        
        # Default to mixed for unclear cases
        return DocumentType.MIXED
    
    async def _identify_knowledge_domains(
        self,
        content: str,
        title: str,
        metadata: Dict[str, Any] = None
    ) -> List[KnowledgeDomain]:
        """Identify knowledge domains for a document"""
        
        domains = []
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Software development
        dev_keywords = ['code', 'programming', 'software', 'api', 'framework', 'library', 'algorithm']
        if any(keyword in content_lower or keyword in title_lower for keyword in dev_keywords):
            domains.append(KnowledgeDomain.SOFTWARE_DEVELOPMENT)
        
        # AI/ML
        ai_keywords = ['machine learning', 'neural network', 'deep learning', 'ai', 'artificial intelligence', 'model']
        if any(keyword in content_lower or keyword in title_lower for keyword in ai_keywords):
            domains.append(KnowledgeDomain.AI_MACHINE_LEARNING)
        
        # Business
        business_keywords = ['business', 'strategy', 'market', 'customer', 'revenue', 'profit', 'growth']
        if any(keyword in content_lower or keyword in title_lower for keyword in business_keywords):
            domains.append(KnowledgeDomain.BUSINESS_STRATEGY)
        
        # Personal knowledge
        personal_keywords = ['personal', 'note', 'reminder', 'journal', 'diary', 'thought']
        if any(keyword in content_lower or keyword in title_lower for keyword in personal_keywords):
            domains.append(KnowledgeDomain.PERSONAL_KNOWLEDGE)
        
        # Research
        research_keywords = ['research', 'study', 'analysis', 'experiment', 'academic', 'paper', 'journal']
        if any(keyword in content_lower or keyword in title_lower for keyword in research_keywords):
            domains.append(KnowledgeDomain.RESEARCH_ACADEMIC)
        
        # Creative
        creative_keywords = ['creative', 'story', 'poem', 'art', 'design', 'writing', 'fiction']
        if any(keyword in content_lower or keyword in title_lower for keyword in creative_keywords):
            domains.append(KnowledgeDomain.CREATIVE_PROJECTS)
        
        # Technical reference
        tech_keywords = ['documentation', 'manual', 'guide', 'reference', 'specification', 'tutorial']
        if any(keyword in content_lower or keyword in title_lower for keyword in tech_keywords):
            domains.append(KnowledgeDomain.TECHNICAL_REFERENCE)
        
        # Default to general if no specific domain identified
        if not domains:
            domains.append(KnowledgeDomain.GENERAL_KNOWLEDGE)
        
        return domains
    
    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content for various metrics"""
        
        # Simple heuristics - in production, use NLP models
        word_count = len(content.split())
        
        # Importance based on length and certain keywords
        importance_keywords = ['important', 'critical', 'key', 'essential', 'priority']
        importance_score = 0.5
        
        if word_count > 1000:
            importance_score += 0.2
        if any(keyword in content.lower() for keyword in importance_keywords):
            importance_score += 0.3
        
        importance_score = min(importance_score, 1.0)
        
        # Complexity based on technical terms and sentence length
        technical_terms = ['algorithm', 'implementation', 'architecture', 'framework', 'methodology']
        complexity_score = 0.5
        
        if any(term in content.lower() for term in technical_terms):
            complexity_score += 0.3
        if word_count > 2000:
            complexity_score += 0.2
        
        complexity_score = min(complexity_score, 1.0)
        
        # Readability (inverse of complexity for simplicity)
        readability_score = 1.0 - complexity_score
        
        return {
            'importance': importance_score,
            'complexity': complexity_score,
            'readability': readability_score,
            'language': 'en',  # Default, could be enhanced with language detection
            'word_count': word_count
        }
    
    async def _generate_multi_context_embeddings(self, document: UniversalDocument):
        """Generate embeddings for different search contexts"""
        
        # This would integrate with sentence-transformers or similar
        # For now, placeholder implementation
        document.embeddings = {
            'general': [0.1] * 384,  # General purpose embedding
            'semantic': [0.2] * 384,  # Semantic similarity
            'code': [0.3] * 384,     # Code-specific embedding if applicable
        }
    
    async def _update_vector_stores(self, document: UniversalDocument):
        """Update vector stores for each relevant domain"""
        
        # Placeholder - would integrate with FAISS stores
        for domain in document.knowledge_domains:
            if domain not in self.vector_stores:
                # Initialize vector store for this domain
                self.vector_stores[domain] = {}
        
        # Add document to relevant vector stores
        # Implementation depends on the chosen vector store backend
        pass
    
    async def _search_vector_store(
        self,
        vector_store,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search in a specific vector store"""
        
        # Placeholder implementation
        # Would integrate with actual vector store (FAISS, etc.)
        
        return []
    
    async def _code_semantic_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Specialized semantic search for code"""
        
        # Placeholder for code-specific search logic
        return []
    
    async def _expand_with_related_documents(
        self,
        initial_results: List[Dict[str, Any]],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Expand search results with related documents"""
        
        # Placeholder for relationship expansion
        return initial_results
    
    async def _intelligent_rerank(
        self,
        results: List[Dict[str, Any]],
        context: SearchContext
    ) -> List[Dict[str, Any]]:
        """Intelligently rerank results based on context"""
        
        # Placeholder for intelligent ranking
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        return {
            'total_documents': len(self.documents),
            'memory_usage_gb': self.memory_usage / (1024 * 1024 * 1024),
            'domain_distribution': {
                domain.value: len(docs) for domain, docs in self.domain_indexes.items()
            },
            'type_distribution': {
                doc_type.value: len(docs) for doc_type, docs in self.type_indexes.items()
            },
            'search_analytics': self.search_analytics,
            'vector_stores': list(self.vector_stores.keys()),
            'storage_path': str(self.storage_path)
        }

# Export
__all__ = ['UniversalRAG', 'SearchContext', 'DocumentType', 'KnowledgeDomain', 'UniversalDocument']