#!/usr/bin/env python3
"""
Model Watcher for AI-Server
Automatically organizes models from /models/ into categorized pool structure
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model-watcher')

class ModelOrganizer(FileSystemEventHandler):
    """Watches /models/ and organizes into /models/pool/ with categories"""
    
    def __init__(self, models_dir: Path, pool_dir: Path):
        self.models_dir = Path(models_dir)
        self.pool_dir = Path(pool_dir)
        self.registry_file = self.models_dir / ".model_registry.json"
        self.registry = self.load_registry()
        
        # Classification rules
        self.classification_rules = {
            'llm/code': ['code', 'coder', 'codegen', 'starcoder', 'codellama'],
            'llm/chat': ['chat', 'instruct', 'conversation', 'dialogue', 'assistant'],
            'llm/general': ['llama', 'mistral', 'mixtral', 'gpt', 'phi'],
            'llm/specialized': ['summary', 'translate', 'medical', 'legal', 'finance'],
            'embedding': ['embed', 'e5', 'bge', 'sentence', 'transformer', 'vector'],
            'multimodal': ['llava', 'vision', 'clip', 'visual', 'image', 'multimodal']
        }
        
        # Initialize pool structure
        self.init_pool_structure()
        
        # Initial scan
        self.scan_and_organize()
    
    def init_pool_structure(self):
        """Create pool directory structure"""
        categories = [
            'llm/code',
            'llm/chat', 
            'llm/general',
            'llm/specialized',
            'embedding',
            'multimodal',
            'uncategorized'
        ]
        
        for category in categories:
            category_path = self.pool_dir / category
            category_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Pool category ready: {category_path}")
    
    def load_registry(self) -> Dict:
        """Load existing model registry"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"models": {}, "links": {}}
    
    def save_registry(self):
        """Save model registry"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2, default=str)
    
    def classify_model(self, path: Path) -> str:
        """Classify model based on name and metadata"""
        name_lower = path.name.lower()
        
        # Check classification rules
        for category, keywords in self.classification_rules.items():
            for keyword in keywords:
                if keyword in name_lower:
                    logger.info(f"🏷️ Classified {path.name} as {category} (keyword: {keyword})")
                    return category
        
        # Check by file size (heuristic)
        try:
            size_gb = path.stat().st_size / (1024**3)
            if size_gb > 5:
                return 'llm/general'  # Large models are probably LLMs
            elif size_gb < 1:
                return 'embedding'    # Small models might be embeddings
        except:
            pass
        
        return 'uncategorized'
    
    def create_pool_copy(self, source: Path) -> Optional[Path]:
        """Create physical copy in pool for a model"""
        if not source.exists() or source.is_dir():
            return None
        
        # Skip if already in pool
        if str(source).startswith(str(self.pool_dir)):
            return None
        
        # Classify model
        category = self.classify_model(source)
        
        # Create destination path
        dest_name = source.name
        dest_path = self.pool_dir / category / dest_name
        
        # Check if already exists with same hash
        if dest_path.exists():
            source_hash = self.get_file_hash(source)
            dest_hash = self.get_file_hash(dest_path)
            if source_hash == dest_hash:
                logger.debug(f"Identical copy already exists: {dest_path}")
                return dest_path
            
            # Handle duplicates with different content
            counter = 1
            stem = source.stem
            suffix = source.suffix
            while dest_path.exists():
                dest_name = f"{stem}_{counter}{suffix}"
                dest_path = self.pool_dir / category / dest_name
                counter += 1
        
        # Copy file
        try:
            import shutil
            logger.info(f"📋 Copying {source.name} to pool ({source.stat().st_size / (1024**3):.2f} GB)...")
            shutil.copy2(source, dest_path)
            logger.info(f"✅ Copied: {source} -> {dest_path}")
            
            # Update registry
            model_hash = self.get_file_hash(dest_path)
            self.registry["models"][model_hash] = {
                "source": str(source),
                "pool_path": str(dest_path),
                "category": category,
                "size": dest_path.stat().st_size,
                "created": datetime.now().isoformat(),
                "name": dest_path.name,
                "original_name": source.name,
                "used_by": []  # Track which apps use this
            }
            self.save_registry()
            self.update_models_readme()
            
            return dest_path
            
        except Exception as e:
            logger.error(f"Failed to copy {source}: {e}")
            return None
    
    def get_file_hash(self, path: Path, chunk_size: int = 8192) -> str:
        """Get hash of first chunk of file for identification"""
        hasher = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                chunk = f.read(chunk_size)
                hasher.update(chunk)
            # Include size for uniqueness
            hasher.update(str(path.stat().st_size).encode())
            return hasher.hexdigest()
        except:
            return hashlib.md5(str(path).encode()).hexdigest()
    
    def update_models_readme(self):
        """Update README.md with model usage information"""
        readme_path = self.models_dir / "README.md"
        
        # Load app configurations
        app_configs = {
            "llm-server": {
                "models": [],
                "purpose": "LLM inference server",
                "preferred": ["deepseek-coder", "llama", "mistral"]
            },
            "memory-server": {
                "models": [],
                "purpose": "RAG and embeddings",
                "preferred": ["sentence-transformers", "bge", "e5"]
            },
            "open-interpreter": {
                "models": [],
                "purpose": "Code execution assistant",
                "preferred": ["deepseek-coder", "codellama", "starcoder"]
            },
            "opencode": {
                "models": [],
                "purpose": "AI Code CLI assistant",
                "preferred": ["deepseek-coder", "codellama", "starcoder", "wizardcoder"]
            }
        }
        
        # Analyze which models are used
        unused_models = []
        
        for model_hash, model_info in self.registry.get("models", {}).items():
            model_name = model_info.get("name", "unknown")
            pool_path = model_info.get("pool_path", "")
            category = model_info.get("category", "")
            size_gb = model_info.get("size", 0) / (1024**3)
            used_by = model_info.get("used_by", [])
            
            if not used_by:
                # Check if any app might want this model
                assigned = False
                for app_name, app_config in app_configs.items():
                    for preferred in app_config["preferred"]:
                        if preferred.lower() in model_name.lower():
                            app_configs[app_name]["models"].append({
                                "name": model_name,
                                "category": category,
                                "size": f"{size_gb:.2f} GB",
                                "status": "configured"
                            })
                            assigned = True
                            break
                    if assigned:
                        break
                
                if not assigned:
                    unused_models.append({
                        "name": model_name,
                        "category": category,
                        "size": f"{size_gb:.2f} GB"
                    })
        
        # Generate README content
        content = f"""# 📦 Models Directory

Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚫 MODELOS SIN USO

"""
        
        if unused_models:
            for model in unused_models:
                content += f"- **{model['name']}** ({model['size']}) - `{model['category']}`\n"
        else:
            content += "_Todos los modelos están asignados a alguna aplicación_\n"
        
        content += "\n## 🔧 MODELOS POR APLICACIÓN\n\n"
        
        for app_name, app_config in app_configs.items():
            content += f"### {app_name.upper()}\n"
            content += f"**Propósito**: {app_config['purpose']}\n\n"
            
            if app_config["models"]:
                for model in app_config["models"]:
                    status_icon = "✅" if model["status"] == "active" else "⚙️"
                    content += f"- {status_icon} **{model['name']}** ({model['size']}) - `{model['category']}`\n"
            else:
                content += "_No hay modelos configurados_\n"
            
            content += "\n"
        
        content += """## 📁 Estructura del Pool

```
models/
├── [tu zona de pruebas]    # Puedes hacer lo que quieras aquí
└── pool/                    # Copias organizadas (no tocar)
    ├── llm/
    │   ├── code/           # Modelos de código
    │   ├── chat/           # Modelos conversacionales
    │   ├── general/        # Propósito general
    │   └── specialized/    # Especializados
    ├── embedding/          # Modelos de embeddings
    ├── multimodal/        # Vision + texto
    └── uncategorized/     # Sin clasificar
```

## 🔄 Estado del Watcher

- **Activo**: Vigilando cambios en `/models/`
- **Intervalo**: Escaneo cada 30 segundos
- **Última actualización**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📝 Notas

- Los modelos en `/models/` son tu zona de pruebas
- Los modelos en `/models/pool/` son copias físicas en servicio
- Puedes borrar todo en `/models/` sin afectar el servicio
- El watcher copiará automáticamente nuevos modelos al pool
"""
        
        # Write README
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"📝 Updated {readme_path}")
    
    def scan_and_organize(self):
        """Scan models directory and organize into pool"""
        logger.info(f"🔍 Scanning {self.models_dir} for models...")
        
        model_extensions = {'.gguf', '.bin', '.pth', '.pt', '.safetensors', '.onnx', '.pb'}
        organized_count = 0
        
        # Find all model files
        for path in self.models_dir.rglob('*'):
            # Skip if in pool directory
            if str(path).startswith(str(self.pool_dir)):
                continue
            
            # Skip directories and non-model files
            if path.is_dir():
                continue
                
            # Check if it's a model file
            if path.suffix.lower() in model_extensions or path.stat().st_size > 100_000_000:  # >100MB
                if self.create_pool_copy(path):
                    organized_count += 1
        
        logger.info(f"✅ Organized {organized_count} models into pool")
        self.print_pool_status()
        self.update_models_readme()
    
    def print_pool_status(self):
        """Print current pool organization status"""
        logger.info("\n📊 Model Pool Status:")
        
        for category_path in sorted(self.pool_dir.rglob("*")):
            if category_path.is_dir():
                models = list(category_path.glob("*"))
                if models:
                    rel_path = category_path.relative_to(self.pool_dir)
                    logger.info(f"  📁 {rel_path}: {len(models)} models")
                    for model in models[:3]:  # Show first 3
                        size_mb = model.stat().st_size / (1024**2) if model.exists() else 0
                        logger.info(f"     - {model.name} ({size_mb:.1f} MB)")
                    if len(models) > 3:
                        logger.info(f"     ... and {len(models)-3} more")
    
    def clean_orphaned_copies(self):
        """Remove pool copies that are no longer needed"""
        # For now, keep all copies as they might be in use
        # In future, could check if models are actively loaded
        pass
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory:
            path = Path(event.src_path)
            # Wait a bit for file to be fully written
            time.sleep(1)
            logger.info(f"📥 New file detected: {path.name}")
            self.create_pool_copy(path)
    
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            path = Path(event.src_path)
            # Check if it's a model file getting downloaded
            if self.is_model_file(path):
                # Wait for download to complete (file size stable)
                if self.wait_for_complete_download(path):
                    logger.info(f"📥 Download complete: {path.name}")
                    self.create_pool_copy(path)
    
    def on_deleted(self, event):
        """Handle file deletion"""
        if not event.is_directory:
            logger.info(f"🗑️ File deleted: {event.src_path}")
            # Note: Pool copies remain intact (that's the point!)
            self.update_models_readme()
    
    def on_moved(self, event):
        """Handle file move"""
        logger.info(f"📦 File moved: {event.src_path} -> {event.dest_path}")
        # Check if it's a new model to copy
        self.create_pool_copy(Path(event.dest_path))
    
    def is_model_file(self, path: Path) -> bool:
        """Check if file is likely a model"""
        model_extensions = {'.gguf', '.bin', '.pth', '.pt', '.safetensors', '.onnx', '.pb'}
        return path.suffix.lower() in model_extensions or path.stat().st_size > 100_000_000
    
    def wait_for_complete_download(self, path: Path, timeout: int = 30) -> bool:
        """Wait for file download to complete"""
        if not path.exists():
            return False
        
        last_size = 0
        stable_count = 0
        
        for _ in range(timeout):
            try:
                current_size = path.stat().st_size
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # Size stable for 3 seconds
                        return True
                else:
                    stable_count = 0
                last_size = current_size
                time.sleep(1)
            except:
                return False
        
        return False

def start_watcher(models_dir: str = None, pool_dir: str = None):
    """Start the model watcher"""
    # Default paths
    if not models_dir:
        models_dir = Path(__file__).parent.parent.parent / "models"
    else:
        models_dir = Path(models_dir)
    
    if not pool_dir:
        pool_dir = models_dir / "pool"
    else:
        pool_dir = Path(pool_dir)
    
    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    pool_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🚀 Starting Model Watcher")
    logger.info(f"📂 Models directory: {models_dir}")
    logger.info(f"🗂️ Pool directory: {pool_dir}")
    
    # Create event handler and observer
    event_handler = ModelOrganizer(models_dir, pool_dir)
    observer = Observer()
    observer.schedule(event_handler, str(models_dir), recursive=True)
    
    # Start watching
    observer.start()
    logger.info(f"👁️ Watching for changes...")
    
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            # Periodic updates
            event_handler.update_models_readme()
    except KeyboardInterrupt:
        observer.stop()
        logger.info("🛑 Watcher stopped")
    
    observer.join()

if __name__ == "__main__":
    start_watcher()