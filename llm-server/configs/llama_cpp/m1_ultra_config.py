"""
M1 Ultra optimized configuration for llama.cpp
Maximizes performance for the M1 Ultra chip with 64 GPU cores and 128GB unified memory
"""

import os
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class M1UltraConfig:
    """Optimized configuration for M1 Ultra hardware"""
    
    # Hardware specifications
    GPU_CORES: int = 64
    UNIFIED_MEMORY_GB: int = 128
    MEMORY_BANDWIDTH_GB_S: float = 800.0  # M1 Ultra bandwidth
    
    # Metal optimization settings
    METAL_ENABLED: bool = True
    GPU_LAYERS: int = -1  # Use all available GPU layers
    
    # Context and batch settings optimized for M1 Ultra
    DEFAULT_CONTEXT_SIZE: int = 8192
    MAX_CONTEXT_SIZE: int = 32768
    BATCH_SIZE: int = 512
    UBATCH_SIZE: int = 512
    
    # Thread configuration
    THREADS: int = 8  # Optimal for M1 Ultra P-cores
    THREADS_BATCH: int = 8
    
    # Memory management
    MEMORY_F16: bool = False  # Use quantized models for efficiency
    MEMORY_MAP: bool = True
    USE_MLOCK: bool = True
    
    # Performance optimizations
    FLASH_ATTENTION: bool = True
    CONT_BATCHING: bool = True
    PARALLEL_REQUESTS: bool = True
    
    # Model-specific optimizations
    MODEL_CONFIGS: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize model-specific configurations"""
        if self.MODEL_CONFIGS is None:
            self.MODEL_CONFIGS = {
                # Router - Ultra fast, minimal resources
                "router": {
                    "n_gpu_layers": -1,
                    "n_ctx": 4096,
                    "n_batch": 256,
                    "n_ubatch": 256,
                    "n_threads": 4,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                },
                
                # Architect - High capability, more resources
                "architect": {
                    "n_gpu_layers": -1,
                    "n_ctx": 16384,
                    "n_batch": 512,
                    "n_ubatch": 512,
                    "n_threads": 8,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                },
                
                # Coders - Balanced performance
                "coder_primary": {
                    "n_gpu_layers": -1,
                    "n_ctx": 8192,
                    "n_batch": 512,
                    "n_ubatch": 512,
                    "n_threads": 6,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                },
                
                "coder_secondary": {
                    "n_gpu_layers": -1,
                    "n_ctx": 8192,
                    "n_batch": 384,
                    "n_ubatch": 384,
                    "n_threads": 6,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                },
                
                # QA Checker - Moderate resources
                "qa_checker": {
                    "n_gpu_layers": -1,
                    "n_ctx": 8192,
                    "n_batch": 384,
                    "n_ubatch": 384,
                    "n_threads": 6,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                },
                
                # Debugger - High precision
                "debugger": {
                    "n_gpu_layers": -1,
                    "n_ctx": 12288,
                    "n_batch": 512,
                    "n_ubatch": 512,
                    "n_threads": 8,
                    "use_mmap": True,
                    "use_mlock": True,
                    "verbose": False,
                    "seed": 42,
                }
            }
    
    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get optimized configuration for specific model type"""
        return self.MODEL_CONFIGS.get(model_type, self.MODEL_CONFIGS["coder_primary"])
    
    def get_memory_usage_gb(self, model_size_b: float) -> float:
        """Estimate memory usage for a model in GB"""
        # Rough estimation: quantized models use ~0.6-0.7 bytes per parameter
        return model_size_b * 0.65 / 1e9
    
    def can_load_model(self, model_size_b: float) -> bool:
        """Check if model can be loaded given current memory usage"""
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        required_memory_gb = self.get_memory_usage_gb(model_size_b)
        return available_memory_gb > required_memory_gb * 1.2  # 20% safety margin
    
    def get_optimal_batch_size(self, model_size_b: float) -> int:
        """Calculate optimal batch size based on model size and available memory"""
        if model_size_b < 2e9:  # < 2B parameters
            return 512
        elif model_size_b < 8e9:  # < 8B parameters
            return 384
        elif model_size_b < 20e9:  # < 20B parameters
            return 256
        else:  # >= 20B parameters
            return 128


def get_llama_cpp_build_config() -> Dict[str, str]:
    """Get environment variables for building llama.cpp with optimal M1 Ultra support"""
    return {
        "CMAKE_ARGS": "-DLLAMA_METAL=ON -DLLAMA_METAL_NDEBUG=ON -DLLAMA_ACCELERATE=ON",
        "FORCE_CMAKE": "1",
        "CMAKE_BUILD_TYPE": "Release",
        "LLAMA_METAL": "1",
        "LLAMA_ACCELERATE": "1",
        "MACOSX_DEPLOYMENT_TARGET": "13.0",  # macOS Ventura for Metal 3 support
    }


def setup_environment():
    """Setup environment variables for optimal M1 Ultra performance"""
    env_vars = get_llama_cpp_build_config()
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Additional runtime optimizations
    os.environ["OMP_NUM_THREADS"] = "8"
    os.environ["MKL_NUM_THREADS"] = "8"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "8"
    
    # Metal specific optimizations
    os.environ["METAL_DEVICE_WRAPPER_TYPE"] = "1"
    os.environ["METAL_DEBUG_ERROR_MODE"] = "0"  # Disable debug for performance


# Global configuration instance
M1_ULTRA_CONFIG = M1UltraConfig()