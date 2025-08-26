"""
RAG Orchestrator implementation for Memory-Server.
Coordinates the complete RAG pipeline workflow.
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional

from ..query_processing import QueryProcessor, QueryRequest
from ..reranker import Reranker, RerankRequest
from ..generation import TextGenerator, GenerationRequest, GenerationMode
from ..hybrid_store import HybridStore
from .models import RAGRequest, RAGResponse, RAGConfig, RAGStage, RAGMode

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Orchestrates the complete RAG pipeline:
    Query Processing → Retrieval → Reranking → Generation
    """
    
    def __init__(
        self, 
        config: Optional[RAGConfig] = None,
        hybrid_store: Optional[HybridStore] = None,
        query_processor: Optional[QueryProcessor] = None,
        reranker: Optional[Reranker] = None,
        text_generator: Optional[TextGenerator] = None
    ):
        self.config = config or RAGConfig()
        
        # Core components
        self.hybrid_store = hybrid_store
        self.query_processor = query_processor
        self.reranker = reranker
        self.text_generator = text_generator
        
        # Initialize components if not provided
        if not self.query_processor and self.config.enable_query_processing:
            self.query_processor = QueryProcessor(text_generator=self.text_generator)
        
        if not self.reranker and self.config.enable_reranking:
            self.reranker = Reranker()
        
        # Conversation memory (simple in-memory storage)
        self.conversation_memory = {}
    
    async def initialize(self):
        """Initialize all RAG components."""
        logger.info("Initializing RAG Orchestrator components")
        
        # Initialize components in parallel
        initialization_tasks = []
        
        if self.query_processor:
            initialization_tasks.append(self.query_processor.initialize())
        
        if self.reranker:
            initialization_tasks.append(self.reranker.initialize())
        
        if self.text_generator:
            initialization_tasks.append(self.text_generator.initialize())
        
        if self.hybrid_store:
            # Assume hybrid store has an initialize method
            if hasattr(self.hybrid_store, 'initialize'):
                initialization_tasks.append(self.hybrid_store.initialize())
        
        # Wait for all components to initialize
        if initialization_tasks:
            await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        logger.info("RAG Orchestrator initialization complete")
    
    async def process(self, request: RAGRequest) -> RAGResponse:
        """
        Process RAG request through the complete pipeline.
        
        Args:
            request: RAG request with query and parameters
            
        Returns:
            RAG response with answer and pipeline metadata
        """
        start_time = time.time()
        current_stage = RAGStage.QUERY_PROCESSING
        
        try:
            # Ensure components are initialized
            await self.initialize()
            
            # Stage 1: Query Processing
            processed_query = None
            if self.config.enable_query_processing and self.query_processor:
                current_stage = RAGStage.QUERY_PROCESSING
                processed_query = await self._process_query(request)
                logger.debug(f"Query processed: {processed_query.processed_query}")
            
            # Stage 2: Retrieval
            current_stage = RAGStage.RETRIEVAL
            retrieved_docs = await self._retrieve_documents(request, processed_query)
            logger.debug(f"Retrieved {len(retrieved_docs)} documents")
            
            if not retrieved_docs:
                return self._create_no_results_response(request, start_time, current_stage)
            
            # Stage 3: Reranking (optional)
            reranked_results = None
            if self.config.enable_reranking and self.reranker and len(retrieved_docs) > 1:
                current_stage = RAGStage.RERANKING
                reranked_results = await self._rerank_documents(request, retrieved_docs, processed_query)
                logger.debug(f"Reranked to top {len(reranked_results)} results")
            
            # Stage 4: Generation
            current_stage = RAGStage.GENERATION
            generation_result = await self._generate_response(request, retrieved_docs, reranked_results, processed_query)
            logger.debug(f"Generated response with {generation_result.token_count} tokens")
            
            # Stage 5: Complete
            current_stage = RAGStage.COMPLETE
            
            # Store in conversation memory if enabled
            if self.config.enable_conversation_memory:
                self._update_conversation_memory(request, generation_result.answer)
            
            # Build final response
            total_time = time.time() - start_time
            sources_used = self._build_sources_metadata(retrieved_docs, reranked_results)
            
            return RAGResponse(
                query=request.query,
                answer=generation_result.answer,
                confidence=self._calculate_overall_confidence(processed_query, generation_result),
                query_processing=processed_query,
                retrieved_documents=retrieved_docs[:request.max_context_docs],
                reranked_results=reranked_results,
                generation_result=generation_result,
                pipeline_stage=current_stage,
                total_time=total_time,
                sources_used=sources_used,
                metadata=request.metadata
            )
            
        except Exception as e:
            logger.error(f"RAG pipeline failed at stage {current_stage}: {e}")
            
            if self.config.fallback_on_error:
                return self._create_fallback_response(request, start_time, current_stage, str(e))
            else:
                raise
    
    async def _process_query(self, request: RAGRequest):
        """Process the user query."""
        query_request = QueryRequest(
            query=request.query,
            workspace=request.workspace,
            metadata=request.metadata
        )
        
        return await self.query_processor.process(query_request)
    
    async def _retrieve_documents(self, request: RAGRequest, processed_query=None) -> List[str]:
        """Retrieve relevant documents."""
        if not self.hybrid_store:
            logger.warning("No hybrid store available for retrieval")
            return []
        
        # Use processed query if available, otherwise original query
        search_query = processed_query.processed_query if processed_query else request.query
        
        try:
            # Perform hybrid search (vector + keyword)
            results = await self.hybrid_store.hybrid_search(
                query=search_query,
                top_k=self.config.default_top_k,
                workspace=request.workspace,
                similarity_threshold=self.config.min_similarity_threshold
            )
            
            # Extract document texts
            documents = [result.get('content', '') for result in results if result.get('content')]
            return documents
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    async def _rerank_documents(self, request: RAGRequest, documents: List[str], processed_query=None) -> List:
        """Rerank retrieved documents."""
        query = processed_query.processed_query if processed_query else request.query
        
        rerank_request = RerankRequest(
            query=query,
            documents=documents,
            top_k=request.max_context_docs
        )
        
        return await self.reranker.rerank(rerank_request)
    
    async def _generate_response(self, request: RAGRequest, documents: List[str], reranked_results=None, processed_query=None):
        """Generate final response."""
        if not self.text_generator:
            raise RuntimeError("No text generator available")
        
        # Use reranked documents if available, otherwise original documents
        context_docs = []
        if reranked_results:
            context_docs = [result.document for result in reranked_results[:request.max_context_docs]]
        else:
            context_docs = documents[:request.max_context_docs]
        
        # Build system prompt based on mode
        system_prompt = self._build_system_prompt(request.mode)
        
        # Add conversation history if available
        if request.conversation_history and self.config.enable_conversation_memory:
            context_docs.append(self._format_conversation_history(request.conversation_history))
        
        generation_request = GenerationRequest(
            query=request.query,
            context=context_docs,
            mode=self._map_rag_mode_to_generation_mode(request.mode),
            system_prompt=system_prompt,
            metadata=request.metadata
        )
        
        return await self.text_generator.generate(generation_request)
    
    def _build_system_prompt(self, mode: RAGMode) -> str:
        """Build system prompt based on RAG mode."""
        base_prompt = "You are a helpful AI assistant. Use the provided context to answer questions accurately and concisely."
        
        if mode == RAGMode.CODE_FOCUSED:
            return base_prompt + " Focus on code-related aspects and provide technical explanations when relevant."
        elif mode == RAGMode.DOCUMENT_FOCUSED:
            return base_prompt + " Focus on document content and provide detailed references."
        elif mode == RAGMode.CONVERSATIONAL:
            return base_prompt + " Maintain a conversational tone and consider previous context."
        elif mode == RAGMode.AGENTIC:
            return base_prompt + " Think step by step and provide reasoning for your answers."
        else:
            return base_prompt
    
    def _map_rag_mode_to_generation_mode(self, rag_mode: RAGMode) -> GenerationMode:
        """Map RAG mode to generation mode."""
        mapping = {
            RAGMode.STANDARD: GenerationMode.RAG_ANSWER,
            RAGMode.CONVERSATIONAL: GenerationMode.RAG_ANSWER,
            RAGMode.CODE_FOCUSED: GenerationMode.CODE_EXPLANATION,
            RAGMode.DOCUMENT_FOCUSED: GenerationMode.RAG_ANSWER,
            RAGMode.AGENTIC: GenerationMode.RAG_ANSWER
        }
        return mapping.get(rag_mode, GenerationMode.RAG_ANSWER)
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history as context."""
        formatted = "Previous conversation:\n"
        for turn in history[-3:]:  # Last 3 turns only
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            formatted += f"{role.title()}: {content}\n"
        return formatted
    
    def _update_conversation_memory(self, request: RAGRequest, answer: str):
        """Update conversation memory."""
        # Simple memory based on workspace
        workspace_key = request.workspace or "default"
        
        if workspace_key not in self.conversation_memory:
            self.conversation_memory[workspace_key] = []
        
        # Add query and answer to memory
        self.conversation_memory[workspace_key].extend([
            {"role": "user", "content": request.query},
            {"role": "assistant", "content": answer}
        ])
        
        # Keep only last 10 turns
        self.conversation_memory[workspace_key] = self.conversation_memory[workspace_key][-10:]
    
    def _build_sources_metadata(self, documents: List[str], reranked_results=None) -> List[Dict[str, Any]]:
        """Build sources metadata for response."""
        sources = []
        
        if reranked_results:
            for i, result in enumerate(reranked_results):
                sources.append({
                    "index": i,
                    "content": result.document[:200] + "..." if len(result.document) > 200 else result.document,
                    "score": result.score,
                    "original_index": result.original_index,
                    "metadata": result.metadata
                })
        else:
            for i, doc in enumerate(documents):
                sources.append({
                    "index": i,
                    "content": doc[:200] + "..." if len(doc) > 200 else doc,
                    "score": None,
                    "original_index": i,
                    "metadata": None
                })
        
        return sources
    
    def _calculate_overall_confidence(self, processed_query=None, generation_result=None) -> float:
        """Calculate overall pipeline confidence."""
        confidences = []
        
        if processed_query:
            confidences.append(processed_query.confidence)
        
        if generation_result:
            confidences.append(generation_result.confidence)
        
        # Average confidence if available, otherwise default
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _create_no_results_response(self, request: RAGRequest, start_time: float, stage: RAGStage) -> RAGResponse:
        """Create response when no documents are retrieved."""
        return RAGResponse(
            query=request.query,
            answer="I couldn't find relevant information to answer your question. Please try rephrasing your query or check if the information exists in the knowledge base.",
            confidence=0.1,
            retrieved_documents=[],
            pipeline_stage=stage,
            total_time=time.time() - start_time,
            sources_used=[],
            metadata=request.metadata
        )
    
    def _create_fallback_response(self, request: RAGRequest, start_time: float, stage: RAGStage, error: str) -> RAGResponse:
        """Create fallback response when pipeline fails."""
        return RAGResponse(
            query=request.query,
            answer="I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.",
            confidence=0.1,
            pipeline_stage=stage,
            total_time=time.time() - start_time,
            sources_used=[],
            error_message=error,
            metadata=request.metadata
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check orchestrator and component health."""
        status = {
            "status": "healthy",
            "components": {}
        }
        
        # Check each component
        if self.query_processor:
            try:
                component_status = await self.query_processor.health_check()
                status["components"]["query_processor"] = component_status
            except Exception as e:
                status["components"]["query_processor"] = {"status": "unhealthy", "error": str(e)}
        
        if self.reranker:
            try:
                component_status = await self.reranker.health_check()
                status["components"]["reranker"] = component_status
            except Exception as e:
                status["components"]["reranker"] = {"status": "unhealthy", "error": str(e)}
        
        if self.text_generator:
            try:
                component_status = await self.text_generator.health_check()
                status["components"]["text_generator"] = component_status
            except Exception as e:
                status["components"]["text_generator"] = {"status": "unhealthy", "error": str(e)}
        
        # Overall health check
        unhealthy_components = [
            name for name, comp_status in status["components"].items() 
            if comp_status.get("status") != "healthy"
        ]
        
        if unhealthy_components:
            status["status"] = "degraded"
            status["unhealthy_components"] = unhealthy_components
        
        # Quick end-to-end test
        try:
            test_request = RAGRequest(query="test query")
            await self.process(test_request)
            status["e2e_test"] = "passed"
        except Exception as e:
            status["status"] = "unhealthy"
            status["e2e_test"] = f"failed: {str(e)}"
        
        return status
    
    async def cleanup(self):
        """Cleanup all components."""
        cleanup_tasks = []
        
        if self.query_processor:
            cleanup_tasks.append(self.query_processor.cleanup())
        
        if self.reranker:
            cleanup_tasks.append(self.reranker.cleanup())
        
        if self.text_generator:
            cleanup_tasks.append(self.text_generator.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Clear conversation memory
        self.conversation_memory.clear()
        
        logger.info("RAG Orchestrator cleanup complete")