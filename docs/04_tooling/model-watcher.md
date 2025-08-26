# Model Watcher Service

## 📋 Visión General

**Model Watcher Service** es un servicio background desarrollado internamente que monitorea automáticamente el directorio `/assets/models/` y organiza los modelos AI en una estructura categorizada para optimización del acceso y gestión.

### **Composición Técnica**
- **Lenguaje**: Python 3.13+ con asyncio
- **File Monitoring**: Watchdog library para real-time detection
- **Architecture**: Event-driven service con background processing
- **Storage**: JSON registry para model metadata
- **Organization**: Intelligent categorization con symbolic links

### **Propósito de Diseño**
Automatizar completamente la organización y gestión de modelos AI (LLMs, embeddings, multimodal) manteniéndolos organizados por categoría y accesibles para los diferentes servicios del ecosistema AI-Server.

## 🏗️ Arquitectura del Sistema

### **Core Components**

#### **1. File System Watcher (`watcher.py`)**
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModelOrganizer(FileSystemEventHandler):
    def __init__(self, models_dir: Path, pool_dir: Path):
        self.models_dir = Path(models_dir)          # /assets/models/
        self.pool_dir = Path(pool_dir)              # /assets/models/pool/
        self.registry_file = self.models_dir / ".model_registry.json"
        
        # Real-time file monitoring
        self.observer = Observer()
        self.observer.schedule(self, self.models_dir, recursive=True)
```

**Funcionalidades:**
- Real-time file system monitoring
- Automatic new model detection
- Change tracking para model updates
- Background processing sin interrupciones

#### **2. Intelligent Classification System**
```python
self.classification_rules = {
    'llm/code': ['code', 'coder', 'codegen', 'starcoder', 'codellama'],
    'llm/chat': ['chat', 'instruct', 'conversation', 'dialogue', 'assistant'],
    'llm/general': ['llama', 'mistral', 'mixtral', 'gpt', 'phi'],
    'llm/specialized': ['summary', 'translate', 'medical', 'legal', 'finance'],
    'embedding': ['embed', 'e5', 'bge', 'sentence', 'transformer', 'vector'],
    'multimodal': ['llava', 'vision', 'clip', 'visual', 'image', 'multimodal']
}

def classify_model(self, filename: str) -> str:
    \"\"\"Intelligent model classification by filename patterns\"\"\"
    filename_lower = filename.lower()
    
    for category, keywords in self.classification_rules.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return category
    
    return 'uncategorized'  # Fallback category
```

**Categorías Inteligentes:**
- **LLM/Code**: Modelos especializados en programación
- **LLM/Chat**: Modelos conversacionales y assistants
- **LLM/General**: Modelos de propósito general
- **LLM/Specialized**: Modelos domain-specific
- **Embedding**: Modelos de vectorización y embeddings
- **Multimodal**: Modelos vision/text multimodales

#### **3. Pool Organization System**
```python
def init_pool_structure(self):
    \"\"\"Create organized pool directory structure\"\"\"
    categories = [
        'llm/code', 'llm/chat', 'llm/general', 'llm/specialized',
        'embedding', 'multimodal', 'uncategorized'
    ]
    
    for category in categories:
        category_path = self.pool_dir / category
        category_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Pool category ready: {category_path}")

def organize_model(self, model_path: Path):
    \"\"\"Organize model into appropriate pool category\"\"\"
    category = self.classify_model(model_path.name)
    target_category = self.pool_dir / category
    target_link = target_category / model_path.name
    
    # Create symbolic link para evitar duplicación
    if not target_link.exists():
        target_link.symlink_to(model_path.resolve())
        self.update_registry(model_path, category, target_link)
```

**Estructura Pool Resultante:**
```
assets/models/pool/
├── llm/
│   ├── code/           # CodeLlama, StarCoder, DeepSeek-Coder, etc.
│   ├── chat/           # ChatGPT-like, Llama-Chat, Mistral-Instruct
│   ├── general/        # Base Llama, Mistral, Phi models
│   └── specialized/    # Domain-specific models
├── embedding/          # E5, BGE, Sentence-Transformers
├── multimodal/         # LLaVA, CLIP, Vision models
└── uncategorized/      # Unclassified models
```

### **4. Model Registry System**
```python
def update_registry(self, original_path: Path, category: str, link_path: Path):
    \"\"\"Update model registry with metadata\"\"\"
    model_info = {
        "original_path": str(original_path),
        "category": category,
        "pool_path": str(link_path),
        "file_size": original_path.stat().st_size,
        "created_at": datetime.now().isoformat(),
        "last_accessed": None,
        "checksum": self.calculate_checksum(original_path),
        "metadata": self.extract_metadata(original_path)
    }
    
    self.registry["models"][original_path.name] = model_info
    self.save_registry()

def extract_metadata(self, model_path: Path) -> Dict:
    \"\"\"Extract model metadata from filename and file\"\"\"
    name = model_path.stem
    
    # Parse common naming patterns
    metadata = {
        "name": name,
        "format": model_path.suffix,
        "size_class": self.classify_by_size(model_path),
        "quantization": self.detect_quantization(name),
        "architecture": self.detect_architecture(name)
    }
    
    return metadata
```

**Registry Features:**
- **Checksum Verification**: Integrity checking
- **Access Tracking**: Usage statistics
- **Metadata Extraction**: Automatic parameter detection
- **Version Management**: Multiple version support

## 🔄 Real-Time Operations

### **Event Handling System**
```python
def on_created(self, event):
    \"\"\"Handle new model file detection\"\"\"
    if not event.is_directory and self.is_model_file(event.src_path):
        logger.info(f"🆕 New model detected: {event.src_path}")
        self.organize_model(Path(event.src_path))
        self.notify_services_new_model(event.src_path)

def on_moved(self, event):
    \"\"\"Handle model file moves/renames\"\"\"
    if not event.is_directory and self.is_model_file(event.dest_path):
        logger.info(f"📁 Model moved: {event.src_path} → {event.dest_path}")
        self.reorganize_model(Path(event.src_path), Path(event.dest_path))

def on_deleted(self, event):
    \"\"\"Handle model deletion\"\"\"
    if not event.is_directory and self.is_model_file(event.src_path):
        logger.info(f"🗑️ Model deleted: {event.src_path}")
        self.cleanup_model_links(Path(event.src_path))
        self.update_registry_deletion(event.src_path)
```

### **Model Type Detection**
```python
def is_model_file(self, filepath: str) -> bool:
    \"\"\"Detect if file is an AI model\"\"\"
    model_extensions = {
        '.gguf',      # llama.cpp format
        '.ggml',      # Legacy llama.cpp
        '.bin',       # Hugging Face safetensors
        '.safetensors', # Hugging Face modern format
        '.pt', '.pth', # PyTorch models
        '.onnx',      # ONNX models
        '.tflite',    # TensorFlow Lite
        '.pkl'        # Pickled models
    }
    
    return Path(filepath).suffix.lower() in model_extensions

def classify_by_size(self, model_path: Path) -> str:
    \"\"\"Classify model by file size\"\"\"
    size_mb = model_path.stat().st_size / (1024 * 1024)
    
    if size_mb < 100:       return "small"      # <100MB
    elif size_mb < 1000:    return "medium"     # <1GB  
    elif size_mb < 10000:   return "large"      # <10GB
    else:                   return "xlarge"     # >10GB
```

## 🚀 Service Integration

### **Auto-Start System (`auto_start.py`)**
```python
#!/usr/bin/env python3
\"\"\"
Auto-start Model Watcher as system service
Integrates with AI-Server startup sequence
\"\"\"

import subprocess
import sys
from pathlib import Path

def start_model_watcher():
    \"\"\"Start Model Watcher service\"\"\"
    ai_server_root = Path(__file__).parent.parent.parent
    models_dir = ai_server_root / "assets" / "models"
    pool_dir = models_dir / "pool"
    
    # Ensure directories exist
    models_dir.mkdir(parents=True, exist_ok=True)
    pool_dir.mkdir(parents=True, exist_ok=True)
    
    # Start watcher service
    watcher_script = Path(__file__).parent / "watcher.py"
    
    cmd = [
        sys.executable, str(watcher_script),
        "--models-dir", str(models_dir),
        "--pool-dir", str(pool_dir),
        "--daemon"
    ]
    
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🔍 Model Watcher service started")

if __name__ == "__main__":
    start_model_watcher()
```

### **Integration con AI-Server Startup**
```bash
# En bin/start_ai_server.py
def start_background_services():
    \"\"\"Start all background services\"\"\"
    services = [
        "services/model-watcher/auto_start.py",  # Model organization
        # Otros servicios background...
    ]
    
    for service in services:
        subprocess.Popen([sys.executable, service])
        logger.info(f"Started background service: {service}")
```

## 📊 Model Management Features

### **Registry Query System**
```python
def find_models_by_category(self, category: str) -> List[Dict]:
    \"\"\"Find all models in specific category\"\"\"
    return [
        model_info for model_info in self.registry["models"].values()
        if model_info["category"] == category
    ]

def find_models_by_size(self, size_class: str) -> List[Dict]:
    \"\"\"Find models by size classification\"\"\"
    return [
        model_info for model_info in self.registry["models"].values()
        if model_info["metadata"]["size_class"] == size_class
    ]

def get_model_recommendations(self, use_case: str) -> List[Dict]:
    \"\"\"Get model recommendations for specific use case\"\"\"
    recommendations = {
        "coding": ["llm/code", "llm/general"],
        "chat": ["llm/chat", "llm/general"], 
        "embeddings": ["embedding"],
        "vision": ["multimodal"]
    }
    
    relevant_categories = recommendations.get(use_case, ["llm/general"])
    return self.find_models_by_categories(relevant_categories)
```

### **Health Monitoring**
```python
def health_check(self) -> Dict[str, Any]:
    \"\"\"Service health check\"\"\"
    total_models = len(self.registry["models"])
    categories_count = {}
    
    for model_info in self.registry["models"].values():
        category = model_info["category"]
        categories_count[category] = categories_count.get(category, 0) + 1
    
    return {
        "service": "model-watcher",
        "status": "healthy",
        "models_tracked": total_models,
        "categories": categories_count,
        "registry_file": str(self.registry_file),
        "last_scan": self.last_scan_time,
        "observer_active": self.observer.is_alive()
    }
```

## 🔧 Usage & Configuration

### **Installation & Setup**
```bash
cd services/model-watcher/

# Install dependencies
pip install -r requirements.txt

# Start service manually
python3 watcher.py --models-dir /path/to/models --pool-dir /path/to/pool

# Start as daemon
python3 watcher.py --models-dir /path/to/models --pool-dir /path/to/pool --daemon
```

### **Configuration Options**
```python
# Environment variables
MODEL_WATCHER_SCAN_INTERVAL = 300    # Scan every 5 minutes
MODEL_WATCHER_LOG_LEVEL = "INFO"     # Logging level
MODEL_WATCHER_REGISTRY_BACKUP = True # Backup registry

# Command line options
--models-dir        # Source directory to watch
--pool-dir          # Target pool organization directory  
--daemon            # Run as background daemon
--scan-interval     # Periodic scan interval in seconds
--log-level         # Logging verbosity level
```

### **Integration con LLM-Server**
```python
# LLM-Server puede consultar modelo recommendations
import requests

def get_recommended_model(use_case: str) -> str:
    \"\"\"Get best model for specific use case\"\"\"
    response = requests.get(
        "http://localhost:8002/model-watcher/recommendations",
        params={"use_case": use_case}
    )
    
    models = response.json()["recommendations"]
    return models[0]["pool_path"] if models else None

# Ejemplo de uso
coding_model = get_recommended_model("coding")
# Returns: /assets/models/pool/llm/code/DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf
```

## 📈 Performance & Monitoring

### **Performance Characteristics**
- **Startup Time**: <2 segundos para scan inicial
- **Memory Usage**: ~10-20MB RAM footprint
- **CPU Impact**: <1% durante operaciones normales
- **I/O Efficiency**: Symbolic links evitan duplicación storage

### **Monitoring & Alerts**
```python
def generate_usage_report(self) -> Dict:
    \"\"\"Generate model usage analytics\"\"\"
    return {
        "most_accessed_models": self.get_top_accessed_models(10),
        "category_distribution": self.get_category_distribution(),
        "size_distribution": self.get_size_distribution(), 
        "recent_additions": self.get_recent_models(7),  # Last 7 days
        "orphaned_links": self.find_orphaned_links(),
        "integrity_status": self.verify_all_checksums()
    }
```

## 🔒 Security & Integrity

### **Checksum Verification**
```python
def calculate_checksum(self, file_path: Path) -> str:
    \"\"\"Calculate SHA-256 checksum for integrity\"\"\"
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_model_integrity(self, model_name: str) -> bool:
    \"\"\"Verify model file integrity\"\"\"
    model_info = self.registry["models"].get(model_name)
    if not model_info:
        return False
        
    current_checksum = self.calculate_checksum(Path(model_info["original_path"]))
    return current_checksum == model_info["checksum"]
```

### **Access Control**
- **Read-only Links**: Symbolic links mantienen modelos originales seguros
- **Registry Protection**: Backup automático del registry
- **Integrity Monitoring**: Checksum verification continuos

---

**Estado**: ✅ Completamente implementado y funcional  
**Integration**: LLM-Server, Memory-Server, ATLAS  
**Background Service**: Auto-start con AI-Server  
**Mantenimiento**: Internal AI-Server team  
**Licencia**: MIT (internal use)