"""
Optimized llama.cpp wrapper for M1 Ultra
Provides high-performance inference with automatic resource management
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, AsyncGenerator, Any
from pathlib import Path
import threading

try:
    from llama_cpp import Llama, LlamaGrammar
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None
    LlamaGrammar = None

from .m1_ultra_config import M1UltraConfig, M1_ULTRA_CONFIG


logger = logging.getLogger(__name__)


class OptimizedLlama:
    """High-performance llama.cpp wrapper optimized for M1 Ultra"""
    
    def __init__(
        self,
        model_path: str = None,
        model_type: str = "coder_primary",
        config: Optional[M1UltraConfig] = None,
        profile: str = "GENERAL",
        auto_detect_profile: bool = True
    ):
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not available. Install with: pip install llama-cpp-python")
        
        self.config = config or M1_ULTRA_CONFIG
        self.model_type = model_type
        self.profile = profile.upper()
        self.auto_detect_profile = auto_detect_profile
        
        # Determine model path
        if model_path is None:
            # Use profile-based model selection
            model_filename = self.config.get_model_by_profile(self.profile)
            models_dir = Path(__file__).parent.parent.parent / "models"
            self.model_path = models_dir / model_filename
        else:
            self.model_path = Path(model_path)
        
        self.llama: Optional[Llama] = None
        self._lock = threading.Lock()
        self._is_loaded = False
        self._load_time: Optional[float] = None
        
        # Get model-specific configuration
        self.model_config = self.config.get_model_config(model_type)
        
    def load_model(self) -> None:
        """Load the model with optimal M1 Ultra settings"""
        if self._is_loaded:
            logger.warning(f"Model {self.model_path.name} already loaded")
            return
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        start_time = time.time()
        logger.info(f"Loading model {self.model_path.name} with config: {self.model_type}")
        
        try:
            self.llama = Llama(
                model_path=str(self.model_path),
                **self.model_config
            )
            
            self._load_time = time.time() - start_time
            self._is_loaded = True
            
            logger.info(
                f"Model {self.model_path.name} loaded successfully in {self._load_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_path.name}: {e}")
            raise
    
    def unload_model(self) -> None:
        """Unload the model and free memory"""
        if self.llama:
            del self.llama
            self.llama = None
            self._is_loaded = False
            logger.info(f"Model {self.model_path.name} unloaded")
    
    def switch_profile_if_needed(self, prompt: str) -> bool:
        """Switch model profile if auto-detection suggests different profile"""
        if not self.auto_detect_profile:
            return False
        
        detected_profile = self.config.detect_profile_from_context(prompt)
        
        if detected_profile != self.profile:
            logger.info(f"Auto-switching from {self.profile} to {detected_profile} profile")
            
            # Unload current model
            if self._is_loaded:
                self.unload_model()
            
            # Update profile and model path
            self.profile = detected_profile
            model_filename = self.config.get_model_by_profile(self.profile)
            models_dir = Path(__file__).parent.parent.parent / "models"
            self.model_path = models_dir / model_filename
            
            return True
        
        return False
    
    async def generate_async(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generation with optimized performance"""
        
        # Auto-switch profile if needed
        self.switch_profile_if_needed(prompt)
        
        if not self._is_loaded:
            self.load_model()
        
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        
        def _generate():
            return self.llama(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                stream=stream,
                **kwargs
            )
        
        if stream:
            # Stream tokens asynchronously
            with self._lock:
                generator = _generate()
                
            for chunk in generator:
                yield chunk
                # Allow other coroutines to run
                await asyncio.sleep(0)
        else:
            # Generate complete response
            with self._lock:
                result = await loop.run_in_executor(None, _generate)
            yield result
    
    def generate_sync(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Synchronous generation for simple use cases"""
        
        # Auto-switch profile if needed
        self.switch_profile_if_needed(prompt)
        
        if not self._is_loaded:
            self.load_model()
        
        with self._lock:
            return self.llama(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                stream=False,
                **kwargs
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and performance metrics"""
        return {
            "model_path": str(self.model_path),
            "model_type": self.model_type,
            "profile": self.profile,
            "auto_detect_profile": self.auto_detect_profile,
            "is_loaded": self._is_loaded,
            "load_time": self._load_time,
            "config": self.model_config,
            "available_profiles": list(self.config.PROFILE_MODELS.keys())
        }
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_loaded
    
    def __enter__(self):
        self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload_model()


class ModelPool:
    """Pool manager for multiple models with automatic loading/unloading"""
    
    def __init__(self, max_models: int = 6):
        self.max_models = max_models
        self.models: Dict[str, OptimizedLlama] = {}
        self.usage_count: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def get_model(
        self, 
        model_id: str, 
        model_path: str = None, 
        model_type: str = "coder_primary",
        profile: str = "GENERAL",
        auto_detect_profile: bool = True
    ) -> OptimizedLlama:
        """Get model from pool, loading if necessary"""
        async with self._lock:
            if model_id not in self.models:
                # Check if we need to unload models
                if len(self.models) >= self.max_models:
                    await self._unload_least_used()
                
                # Load new model
                self.models[model_id] = OptimizedLlama(
                    model_path=model_path,
                    model_type=model_type,
                    profile=profile,
                    auto_detect_profile=auto_detect_profile
                )
                self.usage_count[model_id] = 0
            
            # Update usage and load model if needed
            self.usage_count[model_id] += 1
            
            if not self.models[model_id].is_loaded:
                self.models[model_id].load_model()
            
            return self.models[model_id]
    
    async def _unload_least_used(self):
        """Unload the least used model"""
        if not self.models:
            return
        
        least_used_id = min(self.usage_count.keys(), key=lambda k: self.usage_count[k])
        
        logger.info(f"Unloading least used model: {least_used_id}")
        self.models[least_used_id].unload_model()
        del self.models[least_used_id]
        del self.usage_count[least_used_id]
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status"""
        async with self._lock:
            return {
                "loaded_models": len(self.models),
                "max_models": self.max_models,
                "models": {
                    model_id: {
                        "usage_count": self.usage_count.get(model_id, 0),
                        "is_loaded": model.is_loaded,
                        **model.get_model_info()
                    }
                    for model_id, model in self.models.items()
                }
            }
    
    async def cleanup(self):
        """Cleanup all models"""
        async with self._lock:
            for model in self.models.values():
                model.unload_model()
            self.models.clear()
            self.usage_count.clear()


# Global model pool instance
MODEL_POOL = ModelPool(max_models=6)