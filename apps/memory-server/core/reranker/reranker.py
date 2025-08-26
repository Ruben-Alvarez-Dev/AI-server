"""
Reranker implementation for Memory-Server.
Uses BGE reranker for semantic relevance scoring.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np

try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .models import RerankRequest, RerankResult, RerankerConfig

logger = logging.getLogger(__name__)


class Reranker:
    """Semantic reranker using BGE model."""
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._model_loading = False
        self._model_loaded = False
    
    async def initialize(self):
        """Initialize the reranker model."""
        if self._model_loaded:
            return
            
        if self._model_loading:
            # Wait for model to load if another request is loading it
            while self._model_loading:
                await asyncio.sleep(0.1)
            return
        
        try:
            self._model_loading = True
            logger.info(f"Loading reranker model: {self.config.model_name}")
            
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.error("sentence-transformers not available. Please install it.")
                raise ImportError("sentence-transformers required for reranking")
            
            # Load model in thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_model
            )
            
            self._model_loaded = True
            logger.info("Reranker model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise
        finally:
            self._model_loading = False
    
    def _load_model(self):
        """Load the reranker model synchronously."""
        return CrossEncoder(
            model_name=self.config.model_name,
            device=self.config.device,
            trust_remote_code=self.config.trust_remote_code
        )
    
    async def rerank(self, request: RerankRequest) -> List[RerankResult]:
        """
        Rerank documents based on query relevance.
        
        Args:
            request: Reranking request with query and documents
            
        Returns:
            List of reranked results with scores
        """
        await self.initialize()
        
        if not request.documents:
            return []
        
        try:
            # Prepare query-document pairs
            pairs = [(request.query, doc) for doc in request.documents]
            
            # Run reranking in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                self.executor,
                self._compute_scores,
                pairs
            )
            
            # Create results with metadata
            results = []
            for i, (score, document) in enumerate(zip(scores, request.documents)):
                metadata = None
                if request.metadata and i < len(request.metadata):
                    metadata = request.metadata[i]
                
                results.append(RerankResult(
                    document=document,
                    score=float(score),
                    original_index=i,
                    metadata=metadata
                ))
            
            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Return top_k results
            if request.top_k:
                results = results[:request.top_k]
            
            logger.debug(f"Reranked {len(request.documents)} documents, returning top {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original order with dummy scores
            return self._fallback_results(request)
    
    def _compute_scores(self, pairs: List[tuple]) -> List[float]:
        """Compute reranking scores for query-document pairs."""
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        # Process in batches to manage memory
        batch_size = self.config.batch_size
        all_scores = []
        
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            batch_scores = self.model.predict(batch)
            all_scores.extend(batch_scores.tolist())
        
        return all_scores
    
    def _fallback_results(self, request: RerankRequest) -> List[RerankResult]:
        """Fallback results when reranking fails."""
        results = []
        for i, document in enumerate(request.documents):
            metadata = None
            if request.metadata and i < len(request.metadata):
                metadata = request.metadata[i]
            
            results.append(RerankResult(
                document=document,
                score=0.5,  # Neutral score
                original_index=i,
                metadata=metadata
            ))
        
        if request.top_k:
            results = results[:request.top_k]
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check reranker health status."""
        status = {
            "status": "healthy" if self._model_loaded else "not_ready",
            "model_name": self.config.model_name,
            "model_loaded": self._model_loaded,
            "device": self.config.device
        }
        
        if self._model_loaded:
            # Quick test
            try:
                test_request = RerankRequest(
                    query="test query",
                    documents=["test document"]
                )
                await self.rerank(test_request)
                status["last_test"] = "passed"
            except Exception as e:
                status["status"] = "unhealthy"
                status["last_test"] = f"failed: {str(e)}"
        
        return status
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.model = None
        self._model_loaded = False