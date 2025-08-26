"""
Fusion Layer - Combines Vector and Graph Retrieval Results
Core component for hybrid RAG that merges multiple retrieval strategies
"""

import asyncio
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict

from core.config import get_config
from core.logging_config import get_logger, get_performance_logger
from core.late_chunking import Chunk

logger = get_logger("fusion-layer")
perf_logger = get_performance_logger("fusion-layer")


class FusionStrategy(Enum):
    """Different fusion strategies for combining results"""
    WEIGHTED_SUM = "weighted_sum"
    RRF = "reciprocal_rank_fusion"  # Reciprocal Rank Fusion
    BORDA_COUNT = "borda_count"
    CONDORCET = "condorcet"
    LEARN_TO_RANK = "learn_to_rank"


@dataclass
class RetrievalResult:
    """Standardized retrieval result"""
    id: str
    content: str
    score: float
    source: str  # "vector", "graph", "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk: Optional[Chunk] = None
    graph_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'content': self.content,
            'score': self.score,
            'source': self.source,
            'metadata': self.metadata,
            'has_chunk': self.chunk is not None,
            'has_graph_context': self.graph_context is not None
        }


@dataclass
class FusionConfig:
    """Configuration for fusion operations"""
    strategy: FusionStrategy = FusionStrategy.RRF
    vector_weight: float = 0.6
    graph_weight: float = 0.4
    rrf_k: int = 60  # Parameter for RRF
    min_score_threshold: float = 0.1
    max_results: int = 50
    enable_reranking: bool = True
    reranking_model: Optional[str] = None


class FusionLayer:
    """
    Fusion Layer - Intelligent combination of retrieval results
    
    Combines results from:
    1. Vector similarity search
    2. Knowledge graph traversal  
    3. LazyGraphRAG community detection
    4. Any other retrieval sources
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.app_config = get_config()
        
        # Initialize reranking model if enabled
        self.reranker = None
        if self.config.enable_reranking:
            asyncio.create_task(self._initialize_reranker())
        
        # Performance tracking
        self.stats = {
            'fusions_performed': 0,
            'total_fusion_time': 0.0,
            'avg_vector_results': 0.0,
            'avg_graph_results': 0.0,
            'avg_final_results': 0.0
        }
    
    async def _initialize_reranker(self):
        """Initialize reranking model"""
        try:
            if self.config.reranking_model:
                from sentence_transformers import CrossEncoder
                
                logger.info(f"Loading reranking model: {self.config.reranking_model}")
                
                # Load in thread pool to avoid blocking
                import concurrent.futures
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                
                loop = asyncio.get_event_loop()
                self.reranker = await loop.run_in_executor(
                    executor,
                    lambda: CrossEncoder(self.config.reranking_model)
                )
                
                logger.info("Reranking model loaded successfully")
        
        except Exception as e:
            logger.warning(f"Failed to load reranking model: {e}")
            self.reranker = None
    
    async def fuse_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        query: str,
        additional_sources: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[RetrievalResult]:
        """
        Fuse results from multiple retrieval sources
        
        Args:
            vector_results: Results from vector similarity search
            graph_results: Results from knowledge graph traversal
            query: Original query for reranking
            additional_sources: Additional result sources
        
        Returns:
            Fused and ranked retrieval results
        """
        start_time = time.time()
        
        logger.info(
            "Fusing retrieval results",
            vector_count=len(vector_results),
            graph_count=len(graph_results),
            strategy=self.config.strategy.value
        )
        
        try:
            # Normalize results to common format
            normalized_results = await self._normalize_results(
                vector_results, graph_results, additional_sources or {}
            )
            
            # Apply fusion strategy
            if self.config.strategy == FusionStrategy.WEIGHTED_SUM:
                fused_results = await self._weighted_sum_fusion(normalized_results)
            elif self.config.strategy == FusionStrategy.RRF:
                fused_results = await self._reciprocal_rank_fusion(normalized_results)
            elif self.config.strategy == FusionStrategy.BORDA_COUNT:
                fused_results = await self._borda_count_fusion(normalized_results)
            else:
                # Default to RRF
                fused_results = await self._reciprocal_rank_fusion(normalized_results)
            
            # Apply reranking if enabled
            if self.reranker and query:
                fused_results = await self._rerank_results(fused_results, query)
            
            # Filter and limit results
            final_results = self._filter_and_limit_results(fused_results)
            
            fusion_time = time.time() - start_time
            
            # Update statistics
            self.stats['fusions_performed'] += 1
            self.stats['total_fusion_time'] += fusion_time
            self.stats['avg_vector_results'] = (
                (self.stats['avg_vector_results'] * (self.stats['fusions_performed'] - 1) + len(vector_results)) /
                self.stats['fusions_performed']
            )
            self.stats['avg_graph_results'] = (
                (self.stats['avg_graph_results'] * (self.stats['fusions_performed'] - 1) + len(graph_results)) /
                self.stats['fusions_performed']
            )
            self.stats['avg_final_results'] = (
                (self.stats['avg_final_results'] * (self.stats['fusions_performed'] - 1) + len(final_results)) /
                self.stats['fusions_performed']
            )
            
            perf_logger.log_timing(
                "result_fusion",
                fusion_time,
                vector_results=len(vector_results),
                graph_results=len(graph_results),
                final_results=len(final_results),
                strategy=self.config.strategy.value
            )
            
            logger.info(
                "Result fusion completed",
                final_count=len(final_results),
                fusion_time_ms=round(fusion_time * 1000, 2),
                avg_score=round(np.mean([r.score for r in final_results]), 3) if final_results else 0
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Result fusion failed: {e}")
            # Return best effort results
            return self._create_fallback_results(vector_results, graph_results)
    
    async def _normalize_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]], 
        additional_sources: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[RetrievalResult]]:
        """Normalize all results to common format"""
        
        normalized = {
            'vector': [],
            'graph': [],
        }
        
        # Normalize vector results
        for result in vector_results:
            normalized_result = RetrievalResult(
                id=result.get('id', result.get('chunk_id', str(hash(result.get('content', ''))))),
                content=result.get('content', ''),
                score=float(result.get('score', result.get('similarity_score', 0.0))),
                source='vector',
                metadata=result.get('metadata', {}),
                chunk=result.get('chunk')
            )
            normalized['vector'].append(normalized_result)
        
        # Normalize graph results
        for result in graph_results:
            # Graph results might have different structure
            content = result.get('content', result.get('text', ''))
            score = result.get('score', result.get('relevance', result.get('confidence', 0.0)))
            
            normalized_result = RetrievalResult(
                id=result.get('id', result.get('node_id', str(hash(content)))),
                content=content,
                score=float(score),
                source='graph',
                metadata=result.get('metadata', {}),
                graph_context={
                    'entities': result.get('entities', []),
                    'relations': result.get('relations', []),
                    'path': result.get('path', []),
                    'community': result.get('community')
                }
            )
            normalized['graph'].append(normalized_result)
        
        # Normalize additional sources
        for source_name, results in additional_sources.items():
            normalized[source_name] = []
            for result in results:
                normalized_result = RetrievalResult(
                    id=result.get('id', str(hash(result.get('content', '')))),
                    content=result.get('content', ''),
                    score=float(result.get('score', 0.0)),
                    source=source_name,
                    metadata=result.get('metadata', {})
                )
                normalized[source_name].append(normalized_result)
        
        return normalized
    
    async def _weighted_sum_fusion(
        self, 
        normalized_results: Dict[str, List[RetrievalResult]]
    ) -> List[RetrievalResult]:
        """Fuse results using weighted sum of scores"""
        
        # Collect all unique results
        all_results: Dict[str, RetrievalResult] = {}
        source_weights = {
            'vector': self.config.vector_weight,
            'graph': self.config.graph_weight,
        }
        
        # Add results with weights
        for source, results in normalized_results.items():
            weight = source_weights.get(source, 0.2)  # Default weight for additional sources
            
            for result in results:
                if result.id in all_results:
                    # Combine scores from multiple sources
                    existing = all_results[result.id]
                    existing.score = existing.score + (result.score * weight)
                    existing.source = 'hybrid'
                    
                    # Merge metadata
                    if result.graph_context:
                        existing.graph_context = result.graph_context
                    if result.chunk:
                        existing.chunk = result.chunk
                else:
                    # New result
                    result.score = result.score * weight
                    all_results[result.id] = result
        
        # Sort by combined score
        fused_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return fused_results
    
    async def _reciprocal_rank_fusion(
        self,
        normalized_results: Dict[str, List[RetrievalResult]]
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF)
        Score = sum(1 / (k + rank)) for each source
        """
        
        # Calculate RRF scores
        rrf_scores: Dict[str, float] = defaultdict(float)
        all_results: Dict[str, RetrievalResult] = {}
        
        for source, results in normalized_results.items():
            # Sort by score within source
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
            
            for rank, result in enumerate(sorted_results):
                rrf_score = 1.0 / (self.config.rrf_k + rank + 1)
                rrf_scores[result.id] += rrf_score
                
                if result.id not in all_results:
                    all_results[result.id] = result
                else:
                    # Merge information from multiple sources
                    existing = all_results[result.id]
                    existing.source = 'hybrid'
                    if result.graph_context:
                        existing.graph_context = result.graph_context
                    if result.chunk:
                        existing.chunk = result.chunk
        
        # Apply RRF scores and sort
        for result_id, result in all_results.items():
            result.score = rrf_scores[result_id]
        
        fused_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return fused_results
    
    async def _borda_count_fusion(
        self,
        normalized_results: Dict[str, List[RetrievalResult]]
    ) -> List[RetrievalResult]:
        """Borda Count fusion method"""
        
        borda_scores: Dict[str, int] = defaultdict(int)
        all_results: Dict[str, RetrievalResult] = {}
        
        for source, results in normalized_results.items():
            # Sort by score within source
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
            
            # Assign Borda count points
            for rank, result in enumerate(sorted_results):
                points = len(sorted_results) - rank
                borda_scores[result.id] += points
                
                if result.id not in all_results:
                    all_results[result.id] = result
                else:
                    # Merge information
                    existing = all_results[result.id]
                    existing.source = 'hybrid'
                    if result.graph_context:
                        existing.graph_context = result.graph_context
                    if result.chunk:
                        existing.chunk = result.chunk
        
        # Apply Borda scores (normalize to 0-1 range)
        max_score = max(borda_scores.values()) if borda_scores else 1
        for result_id, result in all_results.items():
            result.score = borda_scores[result_id] / max_score
        
        fused_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return fused_results
    
    async def _rerank_results(
        self, 
        results: List[RetrievalResult], 
        query: str
    ) -> List[RetrievalResult]:
        """Rerank results using cross-encoder model"""
        
        if not self.reranker or not results:
            return results
        
        try:
            logger.info(f"Reranking {len(results)} results")
            
            # Prepare pairs for reranking
            pairs = [(query, result.content) for result in results]
            
            # Get reranking scores in thread pool
            loop = asyncio.get_event_loop()
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                rerank_scores = await loop.run_in_executor(
                    executor,
                    lambda: self.reranker.predict(pairs)
                )
            
            # Apply reranking scores (combine with original scores)
            for i, result in enumerate(results):
                original_score = result.score
                rerank_score = float(rerank_scores[i])
                
                # Weighted combination: 70% rerank + 30% original
                result.score = 0.7 * rerank_score + 0.3 * original_score
                result.metadata['original_score'] = original_score
                result.metadata['rerank_score'] = rerank_score
            
            # Re-sort by new scores
            reranked_results = sorted(results, key=lambda x: x.score, reverse=True)
            
            logger.info(
                "Reranking completed",
                avg_rerank_score=round(np.mean(rerank_scores), 3),
                score_change=round(
                    np.mean([r.score - r.metadata['original_score'] for r in reranked_results]), 3
                )
            )
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results
    
    def _filter_and_limit_results(
        self, 
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Filter by score threshold and limit number of results"""
        
        # Filter by minimum score
        filtered_results = [
            r for r in results 
            if r.score >= self.config.min_score_threshold
        ]
        
        # Remove duplicates based on content similarity
        deduplicated_results = self._deduplicate_results(filtered_results)
        
        # Limit number of results
        limited_results = deduplicated_results[:self.config.max_results]
        
        return limited_results
    
    def _deduplicate_results(
        self, 
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Remove duplicate results based on content similarity"""
        
        if not results:
            return results
        
        deduplicated = []
        seen_content = set()
        
        for result in results:
            # Simple deduplication by content hash
            content_key = hash(result.content[:200])  # First 200 chars
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append(result)
        
        return deduplicated
    
    def _create_fallback_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """Create fallback results when fusion fails"""
        
        fallback_results = []
        
        # Add top vector results
        for i, result in enumerate(vector_results[:10]):
            fallback_result = RetrievalResult(
                id=f"fallback_vector_{i}",
                content=result.get('content', ''),
                score=result.get('score', 0.0) * 0.8,  # Slightly lower score
                source='vector_fallback',
                metadata=result.get('metadata', {})
            )
            fallback_results.append(fallback_result)
        
        # Add top graph results
        for i, result in enumerate(graph_results[:10]):
            fallback_result = RetrievalResult(
                id=f"fallback_graph_{i}",
                content=result.get('content', result.get('text', '')),
                score=result.get('score', 0.0) * 0.8,
                source='graph_fallback',
                metadata=result.get('metadata', {})
            )
            fallback_results.append(fallback_result)
        
        # Sort by score
        return sorted(fallback_results, key=lambda x: x.score, reverse=True)
    
    async def analyze_fusion_effectiveness(
        self,
        vector_results: List[Dict[str, Any]], 
        graph_results: List[Dict[str, Any]],
        fused_results: List[RetrievalResult],
        query: str
    ) -> Dict[str, Any]:
        """Analyze the effectiveness of the fusion"""
        
        analysis = {
            'fusion_strategy': self.config.strategy.value,
            'input_counts': {
                'vector': len(vector_results),
                'graph': len(graph_results)
            },
            'output_count': len(fused_results),
            'coverage': {
                'vector_only': 0,
                'graph_only': 0, 
                'hybrid': 0
            },
            'score_distribution': {
                'min': min([r.score for r in fused_results]) if fused_results else 0,
                'max': max([r.score for r in fused_results]) if fused_results else 0,
                'mean': np.mean([r.score for r in fused_results]) if fused_results else 0,
                'std': np.std([r.score for r in fused_results]) if fused_results else 0
            }
        }
        
        # Count source coverage
        for result in fused_results:
            if result.source == 'vector':
                analysis['coverage']['vector_only'] += 1
            elif result.source == 'graph':
                analysis['coverage']['graph_only'] += 1
            elif result.source == 'hybrid':
                analysis['coverage']['hybrid'] += 1
        
        return analysis
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fusion layer statistics"""
        return {
            **self.stats,
            'avg_fusion_time': (
                self.stats['total_fusion_time'] / 
                max(self.stats['fusions_performed'], 1)
            ),
            'fusion_strategy': self.config.strategy.value,
            'reranking_enabled': self.reranker is not None,
            'config': {
                'vector_weight': self.config.vector_weight,
                'graph_weight': self.config.graph_weight,
                'rrf_k': self.config.rrf_k,
                'min_score_threshold': self.config.min_score_threshold,
                'max_results': self.config.max_results
            }
        }