#!/usr/bin/env python3
"""
Model downloader for LLM Server
Downloads optimized GGUF models for each agent type
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

try:
    from huggingface_hub import hf_hub_download, list_repo_files
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """Downloads and manages GGUF models for the LLM server"""
    
    # Optimized model selections for each agent
    MODEL_SPECS = {
        "router": {
            "repo_id": "Qwen/Qwen2-1.5B-Instruct-GGUF",
            "filename": "qwen2-1_5b-instruct-q6_k.gguf",
            "description": "Ultra-fast routing model",
            "estimated_size_gb": 1.2,
        },
        "architect": {
            "repo_id": "Qwen/Qwen2.5-32B-Instruct-GGUF", 
            "filename": "qwen2.5-32b-instruct-q6_k.gguf",
            "description": "High-capability architecture planning",
            "estimated_size_gb": 22.0,
        },
        "coder_primary": {
            "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
            "filename": "qwen2.5-coder-7b-instruct-q6_k.gguf", 
            "description": "Primary coding model (leader performance)",
            "estimated_size_gb": 5.8,
        },
        "coder_secondary": {
            "repo_id": "LoneStriker/DeepSeek-Coder-V2-Lite-Instruct-GGUF",
            "filename": "DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf",
            "description": "Secondary coding model (MoE efficiency)",
            "estimated_size_gb": 10.5,
        },
        "qa_checker": {
            "repo_id": "Qwen/Qwen2.5-14B-Instruct-GGUF",
            "filename": "qwen2.5-14b-instruct-q6_k.gguf",
            "description": "Quality assurance and testing",
            "estimated_size_gb": 10.2,
        },
        "debugger": {
            "repo_id": "LoneStriker/DeepSeek-Coder-V2-Lite-Instruct-GGUF", 
            "filename": "DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf",
            "description": "Debugging and error analysis",
            "estimated_size_gb": 10.5,
        }
    }
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        if not HF_AVAILABLE:
            raise ImportError("huggingface_hub not available. Install with: pip install huggingface_hub")
    
    def get_model_path(self, model_type: str) -> Path:
        """Get the local path for a model"""
        spec = self.MODEL_SPECS[model_type]
        return self.models_dir / spec["filename"]
    
    def is_model_downloaded(self, model_type: str) -> bool:
        """Check if model is already downloaded"""
        return self.get_model_path(model_type).exists()
    
    async def download_model(self, model_type: str, force: bool = False) -> Path:
        """Download a specific model"""
        if model_type not in self.MODEL_SPECS:
            raise ValueError(f"Unknown model type: {model_type}")
        
        spec = self.MODEL_SPECS[model_type]
        local_path = self.get_model_path(model_type)
        
        if local_path.exists() and not force:
            logger.info(f"Model {model_type} already exists at {local_path}")
            return local_path
        
        logger.info(f"Downloading {spec['description']} ({spec['estimated_size_gb']:.1f}GB)")
        logger.info(f"From: {spec['repo_id']}")
        logger.info(f"File: {spec['filename']}")
        
        try:
            # Download in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(
                None,
                lambda: hf_hub_download(
                    repo_id=spec["repo_id"],
                    filename=spec["filename"],
                    local_dir=str(self.models_dir),
                    local_dir_use_symlinks=False
                )
            )
            
            logger.info(f"Successfully downloaded {model_type} to {downloaded_path}")
            return Path(downloaded_path)
            
        except Exception as e:
            logger.error(f"Failed to download {model_type}: {e}")
            raise
    
    async def download_all_models(self, force: bool = False, skip_large: bool = False):
        """Download all required models"""
        logger.info("Starting download of all required models...")
        
        # Calculate total size
        total_size = sum(spec["estimated_size_gb"] for spec in self.MODEL_SPECS.values())
        logger.info(f"Total estimated download size: {total_size:.1f}GB")
        
        # Check available disk space
        statvfs = os.statvfs(self.models_dir)
        free_space_gb = statvfs.f_frsize * statvfs.f_bavail / (1024**3)
        
        if free_space_gb < total_size * 1.2:  # 20% safety margin
            logger.warning(f"Low disk space! Available: {free_space_gb:.1f}GB, Required: {total_size:.1f}GB")
            if not skip_large:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return
        
        # Download models in order of priority
        priority_order = [
            "router",      # Smallest, most critical
            "coder_primary",  # Primary worker
            "qa_checker",     # Essential for quality
            "debugger",       # Important for fixes
            "coder_secondary", # Backup coder
            "architect"       # Largest, for complex tasks
        ]
        
        for model_type in priority_order:
            spec = self.MODEL_SPECS[model_type]
            
            if skip_large and spec["estimated_size_gb"] > 15:
                logger.info(f"Skipping large model {model_type} ({spec['estimated_size_gb']:.1f}GB)")
                continue
            
            try:
                await self.download_model(model_type, force=force)
            except Exception as e:
                logger.error(f"Failed to download {model_type}: {e}")
                # Continue with other models
                continue
        
        logger.info("Model download process completed!")
    
    def list_available_models(self) -> Dict[str, Dict]:
        """List all available models and their status"""
        models_status = {}
        
        for model_type, spec in self.MODEL_SPECS.items():
            local_path = self.get_model_path(model_type)
            
            models_status[model_type] = {
                "description": spec["description"],
                "estimated_size_gb": spec["estimated_size_gb"],
                "is_downloaded": local_path.exists(),
                "local_path": str(local_path),
                "repo_id": spec["repo_id"],
                "filename": spec["filename"]
            }
        
        return models_status
    
    def print_status(self):
        """Print current model status"""
        logger.info("\n" + "="*60)
        logger.info("MODEL STATUS")
        logger.info("="*60)
        
        models = self.list_available_models()
        total_downloaded = 0
        total_size = 0
        
        for model_type, info in models.items():
            status = "✅ Downloaded" if info["is_downloaded"] else "❌ Not downloaded"
            size_gb = info["estimated_size_gb"]
            
            logger.info(f"{model_type:15} | {size_gb:5.1f}GB | {status} | {info['description']}")
            
            if info["is_downloaded"]:
                total_downloaded += size_gb
            total_size += size_gb
        
        logger.info("-" * 60)
        logger.info(f"Downloaded: {total_downloaded:.1f}GB / {total_size:.1f}GB")
        
        # Show disk usage
        if self.models_dir.exists():
            statvfs = os.statvfs(self.models_dir)
            free_space_gb = statvfs.f_frsize * statvfs.f_bavail / (1024**3)
            logger.info(f"Available disk space: {free_space_gb:.1f}GB")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download LLM Server models")
    parser.add_argument("--models-dir", default="./llm-server/models", help="Models directory")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--skip-large", action="store_true", help="Skip models larger than 15GB")
    parser.add_argument("--model", help="Download specific model only")
    parser.add_argument("--status", action="store_true", help="Show model status")
    
    args = parser.parse_args()
    
    downloader = ModelDownloader(args.models_dir)
    
    if args.status:
        downloader.print_status()
        return
    
    try:
        if args.model:
            if args.model not in downloader.MODEL_SPECS:
                logger.error(f"Unknown model: {args.model}")
                logger.info(f"Available models: {', '.join(downloader.MODEL_SPECS.keys())}")
                sys.exit(1)
            await downloader.download_model(args.model, force=args.force)
        else:
            await downloader.download_all_models(force=args.force, skip_large=args.skip_large)
        
        downloader.print_status()
        
    except KeyboardInterrupt:
        logger.info("Download cancelled by user")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())