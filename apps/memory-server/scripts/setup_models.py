#!/usr/bin/env python3
"""
Memory-Server Model Setup Script
Downloads and configures all necessary models for the system
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Model configurations
MODELS_CONFIG = {
    "embeddings": {
        "primary": "jinaai/jina-embeddings-v2-base-en",
        "colbert": "jinaai/jina-colbert-v2",
        "code": "microsoft/codebert-base",
        "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2"
    },
    "spacy": ["en_core_web_lg", "es_core_news_lg"],
    "nltk": ["punkt", "stopwords", "averaged_perceptron_tagger", "wordnet", "omw-1.4"]
}


def check_requirements():
    """Check if all requirements are met"""
    logger.info("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        logger.error("❌ Python 3.11+ required")
        return False
    
    # Check available disk space (estimate 10GB needed)
    import shutil
    free_space = shutil.disk_usage(MODELS_DIR).free
    required_space = 10 * 1024**3  # 10GB
    
    if free_space < required_space:
        logger.warning(f"⚠️  Low disk space: {free_space / 1024**3:.1f}GB available, {required_space / 1024**3}GB recommended")
    
    logger.info("✅ System requirements check passed")
    return True


def install_python_packages():
    """Install required Python packages"""
    logger.info("📦 Installing Python packages...")
    
    packages = [
        "sentence-transformers==2.5.1",
        "transformers==4.38.0",
        "torch==2.2.0",
        "spacy==3.7.2",
        "nltk==3.8.1",
        "faiss-cpu==1.7.4",
        "networkx==3.2.1"
    ]
    
    for package in packages:
        try:
            logger.info(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install {package}: {e}")
            return False
    
    logger.info("✅ Python packages installed successfully")
    return True


def download_embedding_models():
    """Download embedding models"""
    logger.info("🤖 Downloading embedding models...")
    
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("❌ sentence-transformers not installed")
        return False
    
    for model_type, model_name in MODELS_CONFIG["embeddings"].items():
        try:
            logger.info(f"Downloading {model_type}: {model_name}")
            
            # Download model
            model = SentenceTransformer(model_name)
            
            # Save to local directory
            model_path = MODELS_DIR / model_name.replace("/", "_")
            model.save(str(model_path))
            
            logger.info(f"✅ Saved {model_type} to {model_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
            return False
    
    logger.info("✅ All embedding models downloaded successfully")
    return True


def download_spacy_models():
    """Download spaCy models"""
    logger.info("🔤 Downloading spaCy models...")
    
    for model_name in MODELS_CONFIG["spacy"]:
        try:
            logger.info(f"Downloading spaCy model: {model_name}")
            subprocess.run([
                sys.executable, "-m", "spacy", "download", model_name
            ], check=True)
            logger.info(f"✅ Downloaded {model_name}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
            return False
    
    logger.info("✅ All spaCy models downloaded successfully")
    return True


def download_nltk_data():
    """Download NLTK data"""
    logger.info("📚 Downloading NLTK data...")
    
    try:
        import nltk
    except ImportError:
        logger.error("❌ NLTK not installed")
        return False
    
    for data_name in MODELS_CONFIG["nltk"]:
        try:
            logger.info(f"Downloading NLTK data: {data_name}")
            nltk.download(data_name, quiet=True)
            logger.info(f"✅ Downloaded {data_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {data_name}: {e}")
            return False
    
    logger.info("✅ All NLTK data downloaded successfully")
    return True


def verify_installations():
    """Verify that all models are properly installed"""
    logger.info("🔍 Verifying installations...")
    
    try:
        # Test sentence transformers
        from sentence_transformers import SentenceTransformer
        
        # Test primary embedding model
        primary_model = MODELS_CONFIG["embeddings"]["primary"]
        model = SentenceTransformer(primary_model)
        
        # Test encoding
        test_text = "This is a test sentence."
        embedding = model.encode([test_text])
        
        logger.info(f"✅ Primary embedding model working (dimension: {len(embedding[0])})")
        
        # Test spaCy
        import spacy
        nlp = spacy.load("en_core_web_lg")
        doc = nlp("This is a test.")
        
        logger.info(f"✅ spaCy model working ({len(doc)} tokens processed)")
        
        # Test NLTK
        import nltk
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize("This is a test. This is another test.")
        
        logger.info(f"✅ NLTK working ({len(sentences)} sentences tokenized)")
        
        logger.info("✅ All installations verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def create_config_file():
    """Create initial configuration file"""
    logger.info("⚙️ Creating configuration file...")
    
    config_content = f'''# Memory-Server Configuration
# Generated by setup_models.py

[models]
embedding_model = "{MODELS_CONFIG["embeddings"]["primary"]}"
colbert_model = "{MODELS_CONFIG["embeddings"]["colbert"]}"
code_model = "{MODELS_CONFIG["embeddings"]["code"]}"
reranker_model = "{MODELS_CONFIG["embeddings"]["reranker"]}"

[paths]
models_dir = "{MODELS_DIR}"
data_dir = "{BASE_DIR / 'data'}"
cache_dir = "{BASE_DIR / 'data' / 'cache'}"
logs_dir = "{BASE_DIR / 'data' / 'logs'}"

[performance]
max_context_length = 8192
batch_size = 32
max_concurrent_requests = 100

[memory]
working_memory_size = 131072  # 128K tokens
episodic_memory_size = 2097152  # 2M tokens
'''
    
    config_path = BASE_DIR / "config.ini"
    with open(config_path, "w") as f:
        f.write(config_content)
    
    logger.info(f"✅ Configuration saved to {config_path}")


def main():
    """Main setup function"""
    logger.info("🚀 Starting Memory-Server setup...")
    logger.info("=" * 50)
    
    steps = [
        ("Checking requirements", check_requirements),
        ("Installing Python packages", install_python_packages),
        ("Downloading embedding models", download_embedding_models),
        ("Downloading spaCy models", download_spacy_models),
        ("Downloading NLTK data", download_nltk_data),
        ("Verifying installations", verify_installations),
        ("Creating configuration", create_config_file)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📋 {step_name}...")
        if not step_func():
            logger.error(f"❌ Setup failed at: {step_name}")
            sys.exit(1)
        logger.info(f"✅ {step_name} completed")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 Memory-Server setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Run: python -m pytest tests/ (to run tests)")
    logger.info("2. Run: uvicorn api.main:app --reload (to start server)")
    logger.info("3. Visit: http://localhost:8000/docs (API documentation)")


if __name__ == "__main__":
    main()