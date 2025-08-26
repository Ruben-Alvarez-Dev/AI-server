"""
Text generator implementation for Memory-Server.
Uses Qwen2.5-Coder for RAG response generation.
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .models import GenerationRequest, GenerationResponse, GeneratorConfig, GenerationMode

logger = logging.getLogger(__name__)


class TextGenerator:
    """Text generator using Qwen2.5-Coder model."""
    
    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._model_loading = False
        self._model_loaded = False
    
    async def initialize(self):
        """Initialize the generator model."""
        if self._model_loaded:
            return
            
        if self._model_loading:
            # Wait for model to load if another request is loading it
            while self._model_loading:
                await asyncio.sleep(0.5)
            return
        
        try:
            self._model_loading = True
            logger.info(f"Loading text generator model: {self.config.model_name}")
            
            if not TRANSFORMERS_AVAILABLE:
                logger.error("transformers not available. Please install it.")
                raise ImportError("transformers required for text generation")
            
            # Load model in thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._load_model
            )
            
            self._model_loaded = True
            logger.info("Text generator model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load text generator model: {e}")
            raise
        finally:
            self._model_loading = False
    
    def _load_model(self):
        """Load the generator model synchronously."""
        # Set torch dtype
        torch_dtype = getattr(torch, self.config.torch_dtype) if self.config.torch_dtype != "auto" else "auto"
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            cache_dir=self.config.cache_dir,
            trust_remote_code=self.config.trust_remote_code
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch_dtype,
            device_map=self.config.device if self.config.device != "cpu" else None,
            cache_dir=self.config.cache_dir,
            trust_remote_code=self.config.trust_remote_code
        )
        
        if self.config.device == "cpu":
            self.model = self.model.to("cpu")
        
        # Create generation pipeline
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.config.device == "cuda" else -1
        )
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text response based on query and context.
        
        Args:
            request: Generation request with query and context
            
        Returns:
            Generated response with metadata
        """
        await self.initialize()
        
        start_time = time.time()
        
        try:
            # Build prompt based on mode
            prompt = self._build_prompt(request)
            
            # Run generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            generated_text, token_count = await loop.run_in_executor(
                self.executor,
                self._generate_text,
                prompt,
                request
            )
            
            generation_time = time.time() - start_time
            
            # Calculate confidence (simple heuristic)
            confidence = self._calculate_confidence(generated_text, request)
            
            # Identify sources used (simple heuristic)
            sources_used = self._identify_sources_used(generated_text, request)
            
            return GenerationResponse(
                answer=generated_text,
                confidence=confidence,
                sources_used=sources_used,
                token_count=token_count,
                generation_time=generation_time,
                metadata=request.metadata
            )
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            # Fallback response
            return self._fallback_response(request, time.time() - start_time)
    
    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build prompt based on request mode and context."""
        if request.mode == GenerationMode.RAG_ANSWER:
            return self._build_rag_prompt(request)
        elif request.mode == GenerationMode.SUMMARIZATION:
            return self._build_summary_prompt(request)
        elif request.mode == GenerationMode.QUERY_EXPANSION:
            return self._build_expansion_prompt(request)
        elif request.mode == GenerationMode.CODE_EXPLANATION:
            return self._build_code_prompt(request)
        else:
            return self._build_rag_prompt(request)
    
    def _build_rag_prompt(self, request: GenerationRequest) -> str:
        """Build RAG answer prompt."""
        system_prompt = request.system_prompt or """You are a helpful AI assistant. Use the provided context to answer the user's question accurately and concisely. If the context doesn't contain enough information to answer the question, say so clearly."""
        
        context_text = ""
        if request.context:
            context_text = "\n\nContext:\n" + "\n---\n".join(request.context)
        
        return f"{system_prompt}\n\nQuestion: {request.query}{context_text}\n\nAnswer:"
    
    def _build_summary_prompt(self, request: GenerationRequest) -> str:
        """Build summarization prompt."""
        context_text = "\n".join(request.context) if request.context else ""
        return f"Summarize the following text concisely:\n\n{context_text}\n\nSummary:"
    
    def _build_expansion_prompt(self, request: GenerationRequest) -> str:
        """Build query expansion prompt."""
        return f"Expand this search query with related terms and synonyms: {request.query}\n\nExpanded query:"
    
    def _build_code_prompt(self, request: GenerationRequest) -> str:
        """Build code explanation prompt."""
        context_text = "\n".join(request.context) if request.context else ""
        return f"Explain the following code:\n\n{context_text}\n\nExplanation:"
    
    def _generate_text(self, prompt: str, request: GenerationRequest) -> tuple:
        """Generate text synchronously."""
        if not self.pipeline:
            raise RuntimeError("Model not initialized")
        
        # Generation parameters
        gen_kwargs = {
            "max_new_tokens": request.max_tokens or self.config.max_new_tokens,
            "temperature": request.temperature or self.config.temperature,
            "top_p": self.config.top_p,
            "do_sample": self.config.do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
            "return_full_text": False
        }
        
        # Generate
        result = self.pipeline(prompt, **gen_kwargs)
        generated_text = result[0]["generated_text"].strip()
        
        # Count tokens (approximate)
        token_count = len(self.tokenizer.encode(generated_text))
        
        return generated_text, token_count
    
    def _calculate_confidence(self, text: str, request: GenerationRequest) -> float:
        """Calculate confidence score (simple heuristic)."""
        # Simple heuristics for confidence
        base_confidence = 0.7
        
        # Longer answers tend to be more confident
        if len(text) > 100:
            base_confidence += 0.1
        
        # If we have context, we're more confident
        if request.context and len(request.context) > 0:
            base_confidence += 0.1
        
        # If answer contains uncertainty phrases, reduce confidence
        uncertainty_phrases = ["i don't know", "not sure", "uncertain", "unclear"]
        if any(phrase in text.lower() for phrase in uncertainty_phrases):
            base_confidence -= 0.2
        
        return max(0.1, min(1.0, base_confidence))
    
    def _identify_sources_used(self, text: str, request: GenerationRequest) -> List[int]:
        """Identify which context sources were likely used."""
        if not request.context:
            return []
        
        sources_used = []
        for i, context in enumerate(request.context):
            # Simple overlap check
            context_words = set(context.lower().split())
            text_words = set(text.lower().split())
            overlap = len(context_words.intersection(text_words))
            
            # If significant overlap, assume this source was used
            if overlap > min(10, len(context_words) * 0.3):
                sources_used.append(i)
        
        return sources_used
    
    def _fallback_response(self, request: GenerationRequest, generation_time: float) -> GenerationResponse:
        """Fallback response when generation fails."""
        return GenerationResponse(
            answer="I apologize, but I'm unable to generate a response at this time. Please try again later.",
            confidence=0.1,
            sources_used=[],
            token_count=20,
            generation_time=generation_time,
            metadata=request.metadata
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check generator health status."""
        status = {
            "status": "healthy" if self._model_loaded else "not_ready",
            "model_name": self.config.model_name,
            "model_loaded": self._model_loaded,
            "device": self.config.device
        }
        
        if self._model_loaded:
            # Quick test
            try:
                test_request = GenerationRequest(
                    query="What is AI?",
                    context=["AI stands for Artificial Intelligence."]
                )
                response = await self.generate(test_request)
                status["last_test"] = "passed"
                status["last_test_tokens"] = response.token_count
            except Exception as e:
                status["status"] = "unhealthy"
                status["last_test"] = f"failed: {str(e)}"
        
        return status
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        # Clean up model from memory
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if self.pipeline:
            del self.pipeline
        
        # Clear CUDA cache if using GPU
        if self.config.device == "cuda":
            try:
                torch.cuda.empty_cache()
            except:
                pass
        
        self._model_loaded = False