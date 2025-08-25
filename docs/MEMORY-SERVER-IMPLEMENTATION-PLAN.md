# 🚀 MEMORY-SERVER: Plan de Implementación Detallado

## 📋 Roadmap de Desarrollo

**Duración Total**: 12 días
**Metodología**: Desarrollo incremental modular
**Testing**: Continuo con benchmarks vs R2R

---

## 🎯 FASE 1: Preparación y Setup (Días 1-2)

### **Día 1 - Preparación del Entorno**

#### 1.1 Estructura de Proyecto
```bash
# Crear estructura completa
mkdir -p memory-server/{
    core/{lazy_graph,late_chunking,hybrid_store,agentic_rag},
    memory/{working,episodic,semantic,procedural},
    multimodal/{vision,code,ocr,documents},
    ingestion/{realtime,batch,streaming},
    api/{fastapi,websockets,grpc,graphql},
    tests/{unit,integration,benchmarks},
    data/{vectors,graphs,cache,logs},
    docs/{api,setup,examples},
    scripts/{setup,deploy,monitoring}
}

cd memory-server

# Configurar Git y estructura
git init
echo "# Memory-Server: Next-Gen RAG System" > README.md
```

#### 1.2 Configuración Python y Poetry
```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar Poetry para gestión de dependencias
pip install poetry==1.7.1

# Inicializar pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "memory-server"
version = "1.0.0"
description = "Next-generation RAG system with LazyGraphRAG and Late Chunking"
authors = ["AI-Server Team"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"

# Core ML/AI
sentence-transformers = "^2.5.1"
transformers = "^4.38.0" 
torch = "^2.2.0"
jina = "^3.25.0"

# Vector Stores
faiss-cpu = "^1.7.4"  # M1 optimized
chromadb = "^0.4.22"

# Graph Database
neo4j = "^5.17.0"
networkx = "^3.2.1"
python-igraph = "^0.11.3"

# Text Processing
langchain = "^0.1.9"
langchain-community = "^0.0.20"
spacy = "^3.7.2"
nltk = "^3.8.1"
beautifulsoup4 = "^4.12.3"

# API Framework
fastapi = "^0.109.2"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
websockets = "^12.0"
grpcio = "^1.60.0"
graphql-core = "^3.2.3"

# Async/Performance
asyncio = "^3.4.3"
aiohttp = "^3.9.3"
aiofiles = "^23.2.0"
asyncpg = "^0.29.0"

# Data Processing
pandas = "^2.2.0"
numpy = "^1.26.4"
pyarrow = "^15.0.0"
sqlalchemy = "^2.0.25"

# Computer Vision/OCR
pillow = "^10.2.0"
opencv-python = "^4.9.0"
pytesseract = "^0.3.10"
easyocr = "^1.7.0"

# Monitoring/Logging
prometheus-client = "^0.19.0"
structlog = "^24.1.0"
rich = "^13.7.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.5"
black = "^24.2.0"
isort = "^5.13.2"
mypy = "^1.8.0"
pre-commit = "^3.6.2"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Instalar dependencias
poetry install
```

#### 1.3 Configuración de Pre-commit y Linting
```bash
# Configurar pre-commit
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
EOF

pre-commit install
```

### **Día 2 - Configuración de Modelos y Dependencias**

#### 2.1 Descarga de Modelos Core
```python
# scripts/setup_models.py
"""
Script para descargar y configurar todos los modelos necesarios
"""
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import spacy
import subprocess

MODELS_DIR = Path("data/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def download_embedding_models():
    """Descargar modelos de embeddings"""
    models = [
        "jinaai/jina-embeddings-v2-base-en",
        "jinaai/jina-colbert-v2", 
        "microsoft/codebert-base",
        "sentence-transformers/all-MiniLM-L6-v2",
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ]
    
    for model_name in models:
        print(f"Downloading {model_name}...")
        model = SentenceTransformer(model_name)
        model_path = MODELS_DIR / model_name.replace("/", "_")
        model.save(str(model_path))
        print(f"Saved to {model_path}")

def download_spacy_models():
    """Descargar modelos de spaCy"""
    models = ["en_core_web_lg", "es_core_news_lg"]
    for model in models:
        subprocess.run(["python", "-m", "spacy", "download", model])

def setup_nltk_data():
    """Configurar datos de NLTK"""
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')

if __name__ == "__main__":
    download_embedding_models()
    download_spacy_models() 
    setup_nltk_data()
    print("✅ All models downloaded successfully!")
```

#### 2.2 Configuración Base del Sistema
```python
# core/config.py
"""
Configuración centralizada del sistema
"""
from pathlib import Path
from typing import Dict, Any
import os
from dataclasses import dataclass

@dataclass
class MemoryServerConfig:
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = DATA_DIR / "models"
    CACHE_DIR: Path = DATA_DIR / "cache"
    LOGS_DIR: Path = DATA_DIR / "logs"
    
    # Model Configuration
    EMBEDDING_MODEL: str = "jinaai/jina-embeddings-v2-base-en"
    COLBERT_MODEL: str = "jinaai/jina-colbert-v2" 
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Memory Configuration
    WORKING_MEMORY_SIZE: int = 128 * 1024  # 128K tokens
    EPISODIC_MEMORY_SIZE: int = 2 * 1024 * 1024  # 2M tokens
    SEMANTIC_MEMORY_UNLIMITED: bool = True
    
    # Vector Store
    VECTOR_DIMENSION: int = 768
    FAISS_INDEX_TYPE: str = "HNSW"
    MAX_RESULTS: int = 50
    
    # Graph Configuration
    NEO4J_EMBEDDED: bool = True
    GRAPH_DB_PATH: str = str(DATA_DIR / "neo4j")
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    QUERY_TIMEOUT: int = 30
    BATCH_SIZE: int = 32
    
    # API
    API_HOST: str = "localhost"
    API_PORT: int = 8001  # Different from LLM server
    WEBSOCKET_PORT: int = 8002
    GRPC_PORT: int = 8003

    def __post_init__(self):
        # Crear directorios necesarios
        for path in [self.DATA_DIR, self.MODELS_DIR, self.CACHE_DIR, self.LOGS_DIR]:
            path.mkdir(parents=True, exist_ok=True)

# Instancia global
config = MemoryServerConfig()
```

#### 2.3 Sistema de Logging Estructurado
```python
# core/logging_config.py
"""
Configuración de logging estructurado con Rich y Structlog
"""
import structlog
from rich.console import Console
from rich.logging import RichHandler
import logging
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configurar sistema de logging"""
    
    # Configurar Rich console
    console = Console()
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging standard
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
    
    return structlog.get_logger()

# Logger global
logger = setup_logging()
```

---

## 🔧 FASE 2: Core Components (Días 3-5)

### **Día 3 - LazyGraphRAG Foundation**

#### 3.1 Vector Index Base (Sin pre-procesamiento)
```python
# core/lazy_graph/lazy_indexer.py
"""
Implementación de LazyGraphRAG - Indexación mínima
Basado en Microsoft Research LazyGraphRAG
"""
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import faiss
from core.config import config
from core.logging_config import logger

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: np.ndarray = None

class LazyGraphIndexer:
    """
    LazyGraphRAG Indexer - Solo vectorización, sin grafos pre-construidos
    Costo = 0.1% del GraphRAG tradicional
    """
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.vector_index = None
        self.documents: Dict[str, Document] = {}
        self.dimension = config.VECTOR_DIMENSION
        
    async def initialize(self):
        """Inicializar índice FAISS"""
        logger.info("Initializing LazyGraphRAG indexer")
        
        # Crear índice FAISS HNSW optimizado para M1
        self.vector_index = faiss.IndexHNSWFlat(self.dimension, 32)
        self.vector_index.hnsw.efConstruction = 200
        self.vector_index.hnsw.efSearch = 100
        
        logger.info("LazyGraphRAG indexer initialized")
    
    async def index_document(self, doc: Document) -> str:
        """
        Indexar documento - Solo embedding, NO grafo
        """
        try:
            # Generar embedding
            if doc.embedding is None:
                doc.embedding = await self._generate_embedding(doc.content)
            
            # Agregar al índice vectorial
            self.vector_index.add(doc.embedding.reshape(1, -1))
            
            # Guardar documento
            self.documents[doc.id] = doc
            
            logger.info(f"Document {doc.id} indexed successfully")
            return doc.id
            
        except Exception as e:
            logger.error(f"Error indexing document {doc.id}: {e}")
            raise
    
    async def vector_search(self, query: str, k: int = 20) -> List[Document]:
        """
        Búsqueda vectorial inicial - Primer paso de LazyGraphRAG
        """
        try:
            # Generar embedding de query
            query_embedding = await self._generate_embedding(query)
            
            # Búsqueda en FAISS
            scores, indices = self.vector_index.search(
                query_embedding.reshape(1, -1), k
            )
            
            # Recuperar documentos
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc_id = list(self.documents.keys())[idx]
                    doc = self.documents[doc_id]
                    results.append(doc)
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generar embedding usando Jina"""
        # Usar late chunking si el texto es muy largo
        if len(text) > 8000:  # Cerca del límite de 8192
            return await self._late_chunking_embedding(text)
        
        embedding = self.embedding_model.encode([text])
        return embedding[0]
    
    async def _late_chunking_embedding(self, text: str) -> np.ndarray:
        """
        Late chunking implementation básica
        TODO: Implementar versión completa en Día 4
        """
        # Por ahora, truncar el texto
        truncated = text[:8000]
        embedding = self.embedding_model.encode([truncated])
        return embedding[0]
```

#### 3.2 Dynamic Subgraph Builder
```python
# core/lazy_graph/dynamic_subgraph.py
"""
Construcción dinámica de subgrafos - Core de LazyGraphRAG
"""
import networkx as nx
from typing import List, Set, Dict, Any
import asyncio
import spacy
from collections import defaultdict
from core.lazy_graph.lazy_indexer import Document

class DynamicSubgraphBuilder:
    """
    Construye grafos dinámicamente desde documentos candidatos
    Sin costo de pre-procesamiento
    """
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        
    async def build_subgraph(
        self, 
        documents: List[Document], 
        query: str
    ) -> nx.Graph:
        """
        Construir subgrafo dinámicamente desde documentos
        """
        logger.info(f"Building dynamic subgraph from {len(documents)} documents")
        
        # Crear grafo vacío
        graph = nx.Graph()
        
        # Extraer entidades de todos los documentos en paralelo
        tasks = [
            self._extract_entities_and_relations(doc) 
            for doc in documents
        ]
        extractions = await asyncio.gather(*tasks)
        
        # Construir grafo desde extracciones
        for doc, (entities, relations) in zip(documents, extractions):
            # Agregar nodos (entidades)
            for entity in entities:
                graph.add_node(
                    entity['text'],
                    label=entity['label'],
                    doc_id=doc.id,
                    confidence=entity['confidence']
                )
            
            # Agregar edges (relaciones)
            for relation in relations:
                graph.add_edge(
                    relation['source'],
                    relation['target'],
                    relation_type=relation['type'],
                    weight=relation['weight']
                )
        
        logger.info(f"Dynamic subgraph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
    
    async def _extract_entities_and_relations(
        self, 
        document: Document
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Extraer entidades y relaciones de un documento
        """
        try:
            # Procesar con spaCy
            doc = self.nlp(document.content[:1000000])  # Límite de memoria
            
            # Extraer entidades nombradas
            entities = []
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'confidence': 0.8,  # Default confidence
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            # Extraer relaciones básicas (co-ocurrencia)
            relations = []
            entity_texts = [e['text'] for e in entities]
            
            for i, ent1 in enumerate(entity_texts):
                for ent2 in entity_texts[i+1:]:
                    # Relación por co-ocurrencia en mismo documento
                    relations.append({
                        'source': ent1,
                        'target': ent2,
                        'type': 'co_occurs',
                        'weight': 0.5
                    })
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"Error extracting entities from document {document.id}: {e}")
            return [], []
```

#### 3.3 Community Detection On-Demand
```python
# core/lazy_graph/community_detection.py
"""
Detección de comunidades en tiempo real para LazyGraphRAG
"""
import networkx as nx
from typing import List, Dict, Set
import networkx.algorithms.community as nx_comm
from collections import defaultdict

class CommunityDetector:
    """
    Detección de comunidades para LazyGraphRAG
    Ejecutado on-demand por query
    """
    
    async def detect_communities(self, graph: nx.Graph) -> Dict[int, Set[str]]:
        """
        Detectar comunidades usando algoritmo de Louvain
        """
        try:
            logger.info("Detecting communities in subgraph")
            
            if graph.number_of_nodes() < 2:
                return {0: set(graph.nodes())}
            
            # Usar algoritmo de Louvain para detección de comunidades
            communities = nx_comm.louvain_communities(graph, seed=42)
            
            # Convertir a diccionario
            community_dict = {}
            for i, community in enumerate(communities):
                community_dict[i] = community
            
            logger.info(f"Detected {len(communities)} communities")
            return community_dict
            
        except Exception as e:
            logger.error(f"Error in community detection: {e}")
            # Fallback: cada nodo es su propia comunidad
            return {i: {node} for i, node in enumerate(graph.nodes())}
    
    async def extract_community_context(
        self, 
        community: Set[str], 
        graph: nx.Graph,
        documents: Dict[str, Document]
    ) -> str:
        """
        Extraer contexto relevante de una comunidad
        """
        try:
            # Recopilar contexto de todos los nodos de la comunidad
            context_parts = []
            
            for node in community:
                # Obtener documentos relacionados con este nodo
                node_docs = self._get_node_documents(node, graph, documents)
                
                for doc in node_docs[:3]:  # Máximo 3 docs por nodo
                    # Extraer párrafos relevantes que mencionen el nodo
                    relevant_text = self._extract_relevant_text(
                        node, doc.content
                    )
                    if relevant_text:
                        context_parts.append(relevant_text)
            
            # Combinar contexto (máximo 2000 caracteres)
            combined_context = "\n\n".join(context_parts)
            return combined_context[:2000] + "..." if len(combined_context) > 2000 else combined_context
            
        except Exception as e:
            logger.error(f"Error extracting community context: {e}")
            return ""
    
    def _get_node_documents(
        self, 
        node: str, 
        graph: nx.Graph,
        documents: Dict[str, Document]
    ) -> List[Document]:
        """Obtener documentos asociados con un nodo"""
        node_data = graph.nodes.get(node, {})
        doc_id = node_data.get('doc_id')
        
        if doc_id and doc_id in documents:
            return [documents[doc_id]]
        return []
    
    def _extract_relevant_text(self, entity: str, content: str) -> str:
        """Extraer texto relevante que mencione la entidad"""
        sentences = content.split('.')
        relevant = []
        
        for sentence in sentences:
            if entity.lower() in sentence.lower():
                relevant.append(sentence.strip())
                if len(relevant) >= 3:  # Máximo 3 oraciones
                    break
        
        return '. '.join(relevant)
```

### **Día 4 - Late Chunking Engine**

#### 4.1 Context-Aware Chunking
```python
# core/late_chunking/context_aware_chunker.py
"""
Late Chunking Implementation - Mantiene contexto completo
Basado en JinaAI Late Chunking research
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass
from core.config import config
from core.logging_config import logger

@dataclass
class Chunk:
    content: str
    start_idx: int
    end_idx: int
    embedding: np.ndarray
    token_embeddings: np.ndarray = None  # Para ColBERT-style
    metadata: Dict[str, Any] = None

class LateChunkingEngine:
    """
    Late Chunking Engine - Embeddings ANTES del chunking
    Preserva contexto completo del documento
    """
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.max_context_length = 8192  # Jina v3 limit
        
    async def process_document(
        self, 
        content: str, 
        chunk_size: int = 512,
        overlap: float = 0.2
    ) -> List[Chunk]:
        """
        Procesar documento con Late Chunking
        """
        logger.info(f"Processing document with late chunking (length: {len(content)})")
        
        try:
            # Si el documento es pequeño, no chunking necesario
            if len(content) <= chunk_size:
                embedding = await self._get_full_context_embedding(content)
                return [Chunk(
                    content=content,
                    start_idx=0,
                    end_idx=len(content),
                    embedding=embedding
                )]
            
            # Procesar documento largo con Late Chunking
            return await self._late_chunking_process(content, chunk_size, overlap)
            
        except Exception as e:
            logger.error(f"Error in late chunking: {e}")
            # Fallback a chunking tradicional
            return await self._traditional_chunking(content, chunk_size, overlap)
    
    async def _late_chunking_process(
        self, 
        content: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Chunk]:
        """
        Core Late Chunking Process
        1. Aplicar transformer a TODO el texto
        2. Generar token vectors con contexto completo
        3. Aplicar mean pooling a chunks
        """
        try:
            # Step 1: Procesar TODO el documento con transformer
            # Dividir en segmentos si excede límite de contexto
            segments = self._split_into_segments(content)
            all_chunks = []
            
            for segment in segments:
                # Step 2: Generar embeddings con contexto completo
                token_embeddings = await self._generate_token_embeddings(segment)
                
                # Step 3: Definir boundaries de chunks
                chunk_boundaries = self._calculate_chunk_boundaries(
                    segment, chunk_size, overlap
                )
                
                # Step 4: Aplicar mean pooling a cada chunk
                for start, end in chunk_boundaries:
                    chunk_content = segment[start:end]
                    
                    # Encontrar índices de tokens correspondientes
                    token_start, token_end = self._map_char_to_token_indices(
                        segment, start, end
                    )
                    
                    # Mean pooling de tokens en este chunk
                    chunk_embedding = np.mean(
                        token_embeddings[token_start:token_end], 
                        axis=0
                    )
                    
                    chunk = Chunk(
                        content=chunk_content,
                        start_idx=start,
                        end_idx=end,
                        embedding=chunk_embedding,
                        token_embeddings=token_embeddings[token_start:token_end]
                    )
                    
                    all_chunks.append(chunk)
            
            logger.info(f"Late chunking produced {len(all_chunks)} chunks")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error in late chunking process: {e}")
            raise
    
    async def _generate_token_embeddings(self, text: str) -> np.ndarray:
        """
        Generar embeddings de tokens con contexto completo
        """
        try:
            # Usar el modelo para obtener embeddings de tokens
            # Esto requiere acceso a las capas internas del transformer
            
            # Por ahora, usar sentence embedding como placeholder
            # TODO: Implementar acceso a token embeddings
            sentence_embedding = self.embedding_model.encode([text])
            
            # Simular token embeddings replicando sentence embedding
            # En implementación real, esto vendría de las capas del transformer
            num_tokens = min(len(text.split()), 512)  # Aproximación
            token_embeddings = np.tile(sentence_embedding[0], (num_tokens, 1))
            
            return token_embeddings
            
        except Exception as e:
            logger.error(f"Error generating token embeddings: {e}")
            raise
    
    def _split_into_segments(self, content: str) -> List[str]:
        """
        Dividir contenido en segmentos manejables
        """
        if len(content) <= self.max_context_length:
            return [content]
        
        segments = []
        start = 0
        
        while start < len(content):
            end = min(start + self.max_context_length, len(content))
            
            # Buscar punto de corte natural (final de oración)
            if end < len(content):
                last_period = content.rfind('.', start, end)
                if last_period > start:
                    end = last_period + 1
            
            segments.append(content[start:end])
            start = end
        
        return segments
    
    def _calculate_chunk_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """
        Calcular boundaries de chunks con overlap
        """
        boundaries = []
        text_len = len(text)
        overlap_size = int(chunk_size * overlap)
        
        start = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Buscar punto de corte natural
            if end < text_len:
                # Buscar final de oración
                last_period = text.rfind('.', start, end)
                if last_period > start:
                    end = last_period + 1
                else:
                    # Buscar espacio
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
            
            boundaries.append((start, end))
            
            # Siguiente chunk con overlap
            start = max(start + chunk_size - overlap_size, end)
            
            if start >= text_len:
                break
        
        return boundaries
    
    def _map_char_to_token_indices(
        self, 
        text: str, 
        char_start: int, 
        char_end: int
    ) -> Tuple[int, int]:
        """
        Mapear índices de caracteres a índices de tokens
        Aproximación simple por ahora
        """
        # Aproximación: asumir que los tokens se distribuyen uniformemente
        total_chars = len(text)
        total_tokens = len(text.split())  # Aproximación simple
        
        if total_chars == 0:
            return 0, 0
        
        token_start = int((char_start / total_chars) * total_tokens)
        token_end = int((char_end / total_chars) * total_tokens)
        
        return max(0, token_start), min(total_tokens, token_end)
    
    async def _get_full_context_embedding(self, text: str) -> np.ndarray:
        """
        Obtener embedding con contexto completo para textos pequeños
        """
        embedding = self.embedding_model.encode([text])
        return embedding[0]
    
    async def _traditional_chunking(
        self, 
        content: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Chunk]:
        """
        Chunking tradicional como fallback
        """
        logger.warning("Falling back to traditional chunking")
        
        chunks = []
        overlap_size = int(chunk_size * overlap)
        
        for i in range(0, len(content), chunk_size - overlap_size):
            chunk_content = content[i:i + chunk_size]
            if not chunk_content.strip():
                continue
                
            embedding = await self._get_full_context_embedding(chunk_content)
            
            chunk = Chunk(
                content=chunk_content,
                start_idx=i,
                end_idx=i + len(chunk_content),
                embedding=embedding
            )
            chunks.append(chunk)
        
        return chunks
```

#### 4.2 Semantic Boundary Detection
```python
# core/late_chunking/semantic_boundaries.py
"""
Max-Min Semantic Chunking - Boundaries basados en similitud semántica
"""
import numpy as np
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from core.config import config
from core.logging_config import logger

class SemanticBoundaryDetector:
    """
    Detecta boundaries semánticos usando Max-Min algorithm
    AMI scores: 0.85-0.90 según research
    """
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.similarity_threshold = 0.7  # Configurable
        
    async def detect_semantic_boundaries(
        self, 
        text: str, 
        window_size: int = 3
    ) -> List[int]:
        """
        Detectar boundaries semánticos usando Max-Min algorithm
        """
        logger.info("Detecting semantic boundaries")
        
        try:
            # Dividir en oraciones
            sentences = self._split_into_sentences(text)
            if len(sentences) <= window_size:
                return [0, len(text)]
            
            # Generar embeddings de ventanas
            window_embeddings = await self._generate_window_embeddings(
                sentences, window_size
            )
            
            # Calcular similitud coseno entre ventanas adyacentes
            similarities = self._calculate_similarities(window_embeddings)
            
            # Aplicar Max-Min algorithm para encontrar boundaries
            boundaries = self._max_min_boundary_detection(
                similarities, sentences, text
            )
            
            logger.info(f"Detected {len(boundaries)} semantic boundaries")
            return boundaries
            
        except Exception as e:
            logger.error(f"Error in semantic boundary detection: {e}")
            return [0, len(text)]  # Fallback
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Dividir texto en oraciones"""
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        sentences = nltk.sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _generate_window_embeddings(
        self, 
        sentences: List[str], 
        window_size: int
    ) -> List[np.ndarray]:
        """
        Generar embeddings para ventanas de oraciones
        """
        windows = []
        embeddings = []
        
        for i in range(len(sentences) - window_size + 1):
            # Crear ventana de oraciones
            window = " ".join(sentences[i:i + window_size])
            windows.append(window)
        
        # Generar embeddings en batch
        if windows:
            embeddings = self.embedding_model.encode(windows)
        
        return embeddings
    
    def _calculate_similarities(self, embeddings: List[np.ndarray]) -> List[float]:
        """
        Calcular similitud coseno entre ventanas adyacentes
        """
        similarities = []
        
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i + 1].reshape(1, -1)
            )[0][0]
            similarities.append(sim)
        
        return similarities
    
    def _max_min_boundary_detection(
        self, 
        similarities: List[float], 
        sentences: List[str],
        original_text: str
    ) -> List[int]:
        """
        Max-Min algorithm para detectar boundaries
        """
        boundaries = [0]  # Siempre empezar con 0
        
        # Encontrar mínimos locales en similitudes
        for i in range(1, len(similarities) - 1):
            if (similarities[i] < similarities[i-1] and 
                similarities[i] < similarities[i+1] and
                similarities[i] < self.similarity_threshold):
                
                # Convertir índice de oración a posición en texto
                char_pos = self._sentence_index_to_char_position(
                    i, sentences, original_text
                )
                if char_pos > boundaries[-1]:  # Evitar duplicados
                    boundaries.append(char_pos)
        
        # Agregar final del texto
        if boundaries[-1] != len(original_text):
            boundaries.append(len(original_text))
        
        return boundaries
    
    def _sentence_index_to_char_position(
        self, 
        sentence_idx: int, 
        sentences: List[str],
        original_text: str
    ) -> int:
        """
        Convertir índice de oración a posición de carácter
        """
        if sentence_idx >= len(sentences):
            return len(original_text)
        
        # Buscar la posición de la oración en el texto original
        text_so_far = " ".join(sentences[:sentence_idx + 1])
        return len(text_so_far)
```

### **Día 5 - Hybrid Vector-Graph Store**

#### 5.1 Vector Store con FAISS
```python
# core/hybrid_store/vector_store.py
"""
FAISS Vector Store optimizado para M1 Ultra
"""
import faiss
import numpy as np
import pickle
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import asyncio
from core.config import config
from core.logging_config import logger
from core.late_chunking.context_aware_chunker import Chunk

class VectorStore:
    """
    Vector Store using FAISS with M1 optimizations
    """
    
    def __init__(self):
        self.dimension = config.VECTOR_DIMENSION
        self.index = None
        self.metadata_store: Dict[int, Dict[str, Any]] = {}
        self.id_mapping: Dict[str, int] = {}  # external_id -> faiss_id
        self.reverse_mapping: Dict[int, str] = {}  # faiss_id -> external_id
        self.next_id = 0
        
    async def initialize(self):
        """Inicializar índice FAISS"""
        logger.info("Initializing FAISS vector store")
        
        # Crear índice HNSW optimizado para CPU (M1)
        self.index = faiss.IndexHNSWFlat(self.dimension, 32)  # M = 32
        
        # Configurar parámetros de performance
        self.index.hnsw.efConstruction = 200  # Calidad de construcción
        self.index.hnsw.efSearch = 100        # Calidad de búsqueda
        
        # Para production: usar IndexIVFHNSW para datasets grandes
        # quantizer = faiss.IndexHNSWFlat(self.dimension, 32)
        # self.index = faiss.IndexIVFHNSW(quantizer, self.dimension, 1024, 32)
        
        logger.info("FAISS vector store initialized")
    
    async def add_chunks(self, chunks: List[Chunk], doc_id: str) -> List[str]:
        """
        Agregar chunks al vector store
        """
        try:
            chunk_ids = []
            embeddings = []
            metadata_entries = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Preparar embedding
                if chunk.embedding is not None:
                    embeddings.append(chunk.embedding)
                    
                    # Preparar metadata
                    metadata = {
                        'doc_id': doc_id,
                        'chunk_id': chunk_id,
                        'content': chunk.content,
                        'start_idx': chunk.start_idx,
                        'end_idx': chunk.end_idx,
                        'chunk_metadata': chunk.metadata or {}
                    }
                    metadata_entries.append(metadata)
                    chunk_ids.append(chunk_id)
            
            if embeddings:
                # Convertir a numpy array
                embeddings_array = np.vstack(embeddings).astype('float32')
                
                # Normalizar embeddings (recomendado para cosine similarity)
                faiss.normalize_L2(embeddings_array)
                
                # Agregar al índice
                start_id = self.next_id
                self.index.add(embeddings_array)
                
                # Actualizar mappings y metadata
                for i, (chunk_id, metadata) in enumerate(zip(chunk_ids, metadata_entries)):
                    faiss_id = start_id + i
                    self.id_mapping[chunk_id] = faiss_id
                    self.reverse_mapping[faiss_id] = chunk_id
                    self.metadata_store[faiss_id] = metadata
                
                self.next_id += len(embeddings)
                
                logger.info(f"Added {len(chunks)} chunks to vector store")
            
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
    async def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar vectores similares
        """
        try:
            # Normalizar query embedding
            query_embedding = query_embedding.astype('float32').reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            
            # Buscar en FAISS
            search_k = min(k * 2, 100)  # Buscar más para filtrar
            scores, indices = self.index.search(query_embedding, search_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No hay más resultados
                    break
                    
                if idx in self.metadata_store:
                    metadata = self.metadata_store[idx]
                    
                    # Aplicar filtros si se proporcionan
                    if filters and not self._apply_filters(metadata, filters):
                        continue
                    
                    result = {
                        'id': self.reverse_mapping[idx],
                        'score': float(score),
                        'content': metadata['content'],
                        'metadata': metadata
                    }
                    results.append(result)
                    
                    if len(results) >= k:
                        break
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Aplicar filtros a metadata"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True
    
    async def save(self, path: Path):
        """Guardar índice y metadata"""
        try:
            # Guardar índice FAISS
            faiss.write_index(self.index, str(path / "faiss.index"))
            
            # Guardar metadata
            with open(path / "metadata.pkl", 'wb') as f:
                pickle.dump({
                    'metadata_store': self.metadata_store,
                    'id_mapping': self.id_mapping,
                    'reverse_mapping': self.reverse_mapping,
                    'next_id': self.next_id
                }, f)
            
            logger.info(f"Vector store saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    async def load(self, path: Path):
        """Cargar índice y metadata"""
        try:
            index_path = path / "faiss.index"
            metadata_path = path / "metadata.pkl"
            
            if index_path.exists() and metadata_path.exists():
                # Cargar índice FAISS
                self.index = faiss.read_index(str(index_path))
                
                # Cargar metadata
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata_store = data['metadata_store']
                    self.id_mapping = data['id_mapping']
                    self.reverse_mapping = data['reverse_mapping']
                    self.next_id = data['next_id']
                
                logger.info(f"Vector store loaded from {path}")
            else:
                logger.warning(f"No existing vector store found at {path}")
                await self.initialize()
                
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            await self.initialize()  # Fallback
```

#### 5.2 Knowledge Graph con Neo4j Embedded
```python
# core/hybrid_store/knowledge_graph.py
"""
Knowledge Graph usando Neo4j Embedded (sin Docker)
"""
import asyncio
from typing import List, Dict, Any, Set, Tuple
from neo4j import GraphDatabase
import json
import spacy
from pathlib import Path
from core.config import config
from core.logging_config import logger

class KnowledgeGraph:
    """
    Knowledge Graph local usando Neo4j
    Sin dependencias de Docker
    """
    
    def __init__(self):
        self.driver = None
        self.nlp = spacy.load("en_core_web_lg")
        self.db_path = Path(config.GRAPH_DB_PATH)
        
    async def initialize(self):
        """Inicializar base de datos Neo4j embebida"""
        try:
            logger.info("Initializing Neo4j embedded database")
            
            # Crear directorio si no existe
            self.db_path.mkdir(parents=True, exist_ok=True)
            
            # URI para Neo4j embebido
            uri = f"neo4j://localhost:7687"
            
            # Intentar conectar a Neo4j local
            # En producción: usar Neo4j Embedded real o alternativa como NetworkX
            self.driver = GraphDatabase.driver(
                uri, 
                auth=("neo4j", "password"),
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50,
                connection_acquisition_timeout=2 * 60
            )
            
            # Verificar conexión
            await self._verify_connection()
            
            # Crear índices y constraints
            await self._create_schema()
            
            logger.info("Neo4j knowledge graph initialized")
            
        except Exception as e:
            logger.warning(f"Neo4j not available, using NetworkX fallback: {e}")
            await self._initialize_networkx_fallback()
    
    async def _verify_connection(self):
        """Verificar conexión a Neo4j"""
        with self.driver.session() as session:
            session.run("RETURN 1")
    
    async def _create_schema(self):
        """Crear esquema de la base de datos"""
        constraints = [
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]
        
        indices = [
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX document_source IF NOT EXISTS FOR (d:Document) ON (d.source)",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists or error: {e}")
            
            for index in indices:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index already exists or error: {e}")
    
    async def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """
        Agregar documento y extraer entidades/relaciones
        """
        try:
            logger.info(f"Adding document {doc_id} to knowledge graph")
            
            # Extraer entidades y relaciones
            entities, relations = await self._extract_knowledge(content)
            
            with self.driver.session() as session:
                # Crear nodo de documento
                session.run("""
                    MERGE (d:Document {id: $doc_id})
                    SET d.content = $content,
                        d.metadata = $metadata,
                        d.created_at = datetime()
                """, doc_id=doc_id, content=content[:1000], metadata=json.dumps(metadata))
                
                # Agregar entidades
                for entity in entities:
                    session.run("""
                        MERGE (e:Entity {name: $name})
                        SET e.type = $type,
                            e.confidence = $confidence
                        WITH e
                        MATCH (d:Document {id: $doc_id})
                        MERGE (e)-[:MENTIONED_IN]->(d)
                    """, 
                    name=entity['name'], 
                    type=entity['type'], 
                    confidence=entity['confidence'],
                    doc_id=doc_id)
                
                # Agregar relaciones
                for relation in relations:
                    session.run("""
                        MATCH (e1:Entity {name: $source})
                        MATCH (e2:Entity {name: $target})
                        MERGE (e1)-[r:RELATED_TO]->(e2)
                        SET r.type = $relation_type,
                            r.confidence = $confidence
                    """,
                    source=relation['source'],
                    target=relation['target'],
                    relation_type=relation['type'],
                    confidence=relation['confidence'])
            
            logger.info(f"Added {len(entities)} entities and {len(relations)} relations")
            
        except Exception as e:
            logger.error(f"Error adding document to knowledge graph: {e}")
            raise
    
    async def _extract_knowledge(self, content: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Extraer entidades y relaciones del contenido
        """
        try:
            # Procesar con spaCy
            doc = self.nlp(content[:100000])  # Límite de memoria
            
            entities = []
            entity_positions = {}
            
            # Extraer entidades nombradas
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
                    entity_info = {
                        'name': ent.text,
                        'type': ent.label_,
                        'confidence': 0.8,
                        'start': ent.start_char,
                        'end': ent.end_char
                    }
                    entities.append(entity_info)
                    entity_positions[ent.text] = (ent.start_char, ent.end_char)
            
            # Extraer relaciones basadas en dependencias sintácticas
            relations = []
            for token in doc:
                if token.pos_ == "VERB" and token.dep_ == "ROOT":
                    # Buscar sujeto y objeto
                    subjects = [child for child in token.children if child.dep_ == "nsubj"]
                    objects = [child for child in token.children if child.dep_ in ["dobj", "pobj"]]
                    
                    for subj in subjects:
                        for obj in objects:
                            # Verificar si son entidades nombradas
                            subj_ent = self._find_entity_for_token(subj, entity_positions)
                            obj_ent = self._find_entity_for_token(obj, entity_positions)
                            
                            if subj_ent and obj_ent:
                                relations.append({
                                    'source': subj_ent,
                                    'target': obj_ent,
                                    'type': token.lemma_,
                                    'confidence': 0.6
                                })
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}")
            return [], []
    
    def _find_entity_for_token(self, token, entity_positions: Dict[str, Tuple[int, int]]) -> Optional[str]:
        """Encontrar entidad que contiene el token"""
        for entity_name, (start, end) in entity_positions.items():
            if start <= token.idx < end:
                return entity_name
        return None
    
    async def search_graph(
        self, 
        query: str, 
        max_hops: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Buscar en el grafo de conocimiento
        """
        try:
            # Extraer entidades de la query
            query_doc = self.nlp(query)
            query_entities = [ent.text for ent in query_doc.ents if ent.label_ in 
                            ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']]
            
            if not query_entities:
                # Fallback: búsqueda por texto
                return await self._text_search(query, limit)
            
            results = []
            with self.driver.session() as session:
                for entity in query_entities[:3]:  # Max 3 entidades
                    cypher = f"""
                    MATCH (e:Entity {{name: $entity_name}})
                    CALL {{
                        WITH e
                        MATCH (e)-[*1..{max_hops}]-(related)-[:MENTIONED_IN]->(d:Document)
                        RETURN d, related, e
                        LIMIT {limit}
                    }}
                    RETURN d.id as doc_id, d.content as content, 
                           collect(related.name) as related_entities
                    """
                    
                    result = session.run(cypher, entity_name=entity)
                    
                    for record in result:
                        results.append({
                            'doc_id': record['doc_id'],
                            'content': record['content'],
                            'related_entities': record['related_entities'],
                            'source': 'knowledge_graph',
                            'query_entity': entity
                        })
            
            logger.info(f"Graph search returned {len(results)} results")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in graph search: {e}")
            return []
    
    async def _text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Búsqueda de texto fallback"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                WHERE d.content CONTAINS $query
                RETURN d.id as doc_id, d.content as content
                LIMIT $limit
            """, query=query, limit=limit)
            
            return [{
                'doc_id': record['doc_id'],
                'content': record['content'],
                'source': 'text_search'
            } for record in result]
    
    async def close(self):
        """Cerrar conexión"""
        if self.driver:
            self.driver.close()
    
    # Fallback usando NetworkX si Neo4j no está disponible
    async def _initialize_networkx_fallback(self):
        """Inicializar fallback con NetworkX"""
        import networkx as nx
        import pickle
        
        logger.info("Initializing NetworkX fallback for knowledge graph")
        
        self.graph = nx.MultiDiGraph()
        self.documents = {}
        self.entity_docs = {}
        
        # Intentar cargar grafo existente
        graph_file = self.db_path / "networkx_graph.pkl"
        if graph_file.exists():
            try:
                with open(graph_file, 'rb') as f:
                    data = pickle.load(f)
                    self.graph = data.get('graph', nx.MultiDiGraph())
                    self.documents = data.get('documents', {})
                    self.entity_docs = data.get('entity_docs', {})
                logger.info("Loaded existing NetworkX graph")
            except Exception as e:
                logger.error(f"Error loading NetworkX graph: {e}")
        
        logger.info("NetworkX knowledge graph fallback initialized")
```

---

## ⚡ FASE 3: Advanced Features (Días 6-8)

### **Día 6 - Agentic RAG Implementation**

#### 6.1 Multi-Turn Reasoning Engine
```python
# core/agentic_rag/multi_turn_reasoning.py
"""
Agentic RAG con Think-Retrieve-Rethink-Generate Loop
Basado en Graph-R1 research
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from core.config import config
from core.logging_config import logger
from core.hybrid_store.vector_store import VectorStore
from core.hybrid_store.knowledge_graph import KnowledgeGraph
from sentence_transformers import SentenceTransformer

class ReasoningState(Enum):
    THINKING = "thinking"
    RETRIEVING = "retrieving"
    RETHINKING = "rethinking"
    GENERATING = "generating"
    COMPLETE = "complete"

@dataclass
class ReasoningStep:
    step_number: int
    state: ReasoningState
    query: str
    refined_query: Optional[str]
    retrieved_docs: List[Dict[str, Any]]
    analysis: str
    confidence: float
    decision: str  # "continue" or "terminate"

@dataclass
class AgenticRAGResult:
    original_query: str
    steps: List[ReasoningStep]
    final_answer: str
    total_confidence: float
    reasoning_chain: str

class MultiTurnReasoningEngine:
    """
    Engine de razonamiento multi-turno para Agentic RAG
    Implementa el paradigma Think-Retrieve-Rethink-Generate
    """
    
    def __init__(
        self, 
        vector_store: VectorStore, 
        knowledge_graph: KnowledgeGraph,
        max_turns: int = 5
    ):
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.max_turns = max_turns
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Prompts para cada fase del razonamiento
        self.thinking_prompt = """
You are an AI reasoning agent. Analyze the user's question and determine what information you need to answer it effectively.

User Question: {query}
Current Knowledge: {current_knowledge}
Previous Attempts: {previous_attempts}

Think through:
1. What specific information is needed to answer this question?
2. What knowledge gaps exist in the current information?
3. What should be the next search strategy?
4. Is the current information sufficient to provide a complete answer?

Provide your analysis and next search query:
Analysis:
Search Query:
Confidence (0-1):
Decision (continue/terminate):
"""
        
        self.analysis_prompt = """
Analyze the retrieved information for relevance and completeness.

Original Question: {query}
Retrieved Information:
{retrieved_docs}

Analyze:
1. How relevant is this information to the original question?
2. What new insights does it provide?
3. What information is still missing?
4. Should we continue searching or is this sufficient?

Analysis:
Relevance Score (0-1):
Completeness Score (0-1):
Missing Information:
Decision (continue/terminate):
"""
        
        self.synthesis_prompt = """
Based on all the information gathered through multiple reasoning steps, provide a comprehensive answer.

Original Question: {query}

Reasoning Chain:
{reasoning_chain}

Retrieved Information:
{all_retrieved_docs}

Synthesize a complete, accurate answer that:
1. Directly addresses the original question
2. Uses evidence from multiple sources
3. Shows logical reasoning
4. Acknowledges any limitations or uncertainties

Answer:
"""
    
    async def reason(self, query: str, context: Dict[str, Any] = None) -> AgenticRAGResult:
        """
        Execute multi-turn reasoning process
        """
        logger.info(f"Starting agentic reasoning for query: {query}")
        
        result = AgenticRAGResult(
            original_query=query,
            steps=[],
            final_answer="",
            total_confidence=0.0,
            reasoning_chain=""
        )
        
        current_knowledge = []
        all_retrieved_docs = []
        current_query = query
        
        # Multi-turn reasoning loop
        for turn in range(self.max_turns):
            logger.info(f"Reasoning turn {turn + 1}/{self.max_turns}")
            
            # THINK: Analyze what information is needed
            thinking_result = await self._think(
                current_query, 
                current_knowledge, 
                result.steps
            )
            
            step = ReasoningStep(
                step_number=turn + 1,
                state=ReasoningState.THINKING,
                query=current_query,
                refined_query=thinking_result['refined_query'],
                retrieved_docs=[],
                analysis=thinking_result['analysis'],
                confidence=thinking_result['confidence'],
                decision=thinking_result['decision']
            )
            
            # RETRIEVE: Search for information
            if step.decision == "continue":
                step.state = ReasoningState.RETRIEVING
                retrieved_docs = await self._retrieve(
                    thinking_result['refined_query'] or current_query
                )
                step.retrieved_docs = retrieved_docs
                all_retrieved_docs.extend(retrieved_docs)
                
                # RETHINK: Analyze retrieved information
                step.state = ReasoningState.RETHINKING
                analysis_result = await self._rethink(
                    query, retrieved_docs, all_retrieved_docs
                )
                
                step.analysis += f"\n\nRethinking: {analysis_result['analysis']}"
                step.confidence = (step.confidence + analysis_result['relevance']) / 2
                step.decision = analysis_result['decision']
                
                # Update current knowledge
                current_knowledge.extend([
                    doc['content'] for doc in retrieved_docs[:3]
                ])
                
                # Prepare next query if continuing
                if step.decision == "continue" and turn < self.max_turns - 1:
                    current_query = analysis_result.get('next_query', current_query)
            
            result.steps.append(step)
            
            # Decide whether to continue
            if step.decision == "terminate" or step.confidence > 0.9:
                logger.info(f"Reasoning terminated after {turn + 1} turns")
                break
        
        # GENERATE: Synthesize final answer
        result.final_answer = await self._generate_final_answer(
            query, result.steps, all_retrieved_docs
        )
        
        result.total_confidence = self._calculate_total_confidence(result.steps)
        result.reasoning_chain = self._build_reasoning_chain(result.steps)
        
        logger.info(f"Agentic reasoning completed with confidence: {result.total_confidence:.2f}")
        return result
    
    async def _think(
        self, 
        query: str, 
        current_knowledge: List[str], 
        previous_steps: List[ReasoningStep]
    ) -> Dict[str, Any]:
        """
        THINK phase: Analyze what information is needed
        """
        try:
            # Preparar contexto
            knowledge_summary = "\n".join(current_knowledge[-3:])  # Últimos 3
            previous_summary = "\n".join([
                f"Step {s.step_number}: {s.analysis}" for s in previous_steps[-2:]
            ])
            
            # Generar prompt
            prompt = self.thinking_prompt.format(
                query=query,
                current_knowledge=knowledge_summary,
                previous_attempts=previous_summary
            )
            
            # En una implementación real, esto iría al LLM
            # Por ahora, simulamos el razonamiento
            
            # Análisis simple basado en palabras clave
            analysis = await self._simple_analysis(query, current_knowledge)
            
            return {
                'analysis': analysis['reasoning'],
                'refined_query': analysis['refined_query'],
                'confidence': analysis['confidence'],
                'decision': analysis['decision']
            }
            
        except Exception as e:
            logger.error(f"Error in thinking phase: {e}")
            return {
                'analysis': "Error in analysis",
                'refined_query': query,
                'confidence': 0.3,
                'decision': "continue"
            }
    
    async def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        RETRIEVE phase: Multi-strategy retrieval
        """
        try:
            # Generar embedding para query
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Búsqueda vectorial
            vector_results = await self.vector_store.search(
                query_embedding, k=10
            )
            
            # Búsqueda en grafo de conocimiento
            graph_results = await self.knowledge_graph.search_graph(
                query, max_hops=2, limit=10
            )
            
            # Combinar y deduplica resultados
            all_results = vector_results + graph_results
            unique_results = self._deduplicate_results(all_results)
            
            # Reranking por relevancia
            ranked_results = await self._rerank_results(query, unique_results)
            
            return ranked_results[:15]  # Top 15
            
        except Exception as e:
            logger.error(f"Error in retrieval phase: {e}")
            return []
    
    async def _rethink(
        self, 
        original_query: str, 
        retrieved_docs: List[Dict[str, Any]],
        all_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        RETHINK phase: Analyze retrieved information
        """
        try:
            # Evaluar relevancia de documentos
            relevance_scores = []
            for doc in retrieved_docs:
                score = await self._calculate_relevance(original_query, doc['content'])
                relevance_scores.append(score)
            
            avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.0
            
            # Determinar si es suficiente información
            total_docs = len(all_docs)
            unique_sources = len(set(doc.get('doc_id', '') for doc in all_docs))
            
            # Heurística para decisión
            if avg_relevance > 0.7 and total_docs >= 5:
                decision = "terminate"
            elif total_docs >= 20:
                decision = "terminate"  # Evitar búsquedas infinitas
            else:
                decision = "continue"
            
            # Generar siguiente query si continuamos
            next_query = await self._generate_next_query(
                original_query, retrieved_docs
            ) if decision == "continue" else None
            
            analysis = f"""
            Retrieved {len(retrieved_docs)} documents.
            Average relevance: {avg_relevance:.2f}
            Total documents so far: {total_docs}
            Unique sources: {unique_sources}
            Decision: {decision}
            """
            
            return {
                'analysis': analysis,
                'relevance': avg_relevance,
                'decision': decision,
                'next_query': next_query
            }
            
        except Exception as e:
            logger.error(f"Error in rethinking phase: {e}")
            return {
                'analysis': "Error in analysis",
                'relevance': 0.3,
                'decision': "terminate"
            }
    
    async def _generate_final_answer(
        self, 
        query: str, 
        steps: List[ReasoningStep], 
        all_docs: List[Dict[str, Any]]
    ) -> str:
        """
        GENERATE phase: Synthesize final answer
        """
        try:
            # Construir cadena de razonamiento
            reasoning_chain = "\n".join([
                f"Step {s.step_number}: {s.analysis}" for s in steps
            ])
            
            # Extraer contenido más relevante
            relevant_content = []
            for doc in all_docs[:10]:  # Top 10 documentos
                if len(doc.get('content', '')) > 50:  # Filtrar contenido muy corto
                    relevant_content.append(doc['content'][:500])  # Truncar
            
            docs_summary = "\n\n".join(relevant_content)
            
            # En implementación real, esto iría al LLM
            # Por ahora, generar respuesta simple
            answer = await self._synthesize_simple_answer(
                query, reasoning_chain, docs_summary
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating final answer: {e}")
            return "I apologize, but I encountered an error while generating the final answer."
    
    # Métodos auxiliares simplificados para simulación
    
    async def _simple_analysis(
        self, 
        query: str, 
        knowledge: List[str]
    ) -> Dict[str, Any]:
        """Análisis simple de la query"""
        
        # Palabras clave que indican necesidad de más información
        complex_keywords = ['how', 'why', 'what', 'compare', 'analyze', 'explain']
        needs_more_info = any(keyword in query.lower() for keyword in complex_keywords)
        
        # Si no tenemos conocimiento previo, necesitamos buscar
        if not knowledge:
            return {
                'reasoning': "No prior knowledge available. Need to search for information.",
                'refined_query': query,
                'confidence': 0.2,
                'decision': 'continue'
            }
        
        # Si tenemos algo de información pero la query es compleja
        if needs_more_info and len(knowledge) < 3:
            return {
                'reasoning': f"Query appears complex. Current knowledge: {len(knowledge)} pieces. Need more information.",
                'refined_query': f"detailed information about {query}",
                'confidence': 0.4,
                'decision': 'continue'
            }
        
        # Si tenemos suficiente información
        return {
            'reasoning': f"Have {len(knowledge)} pieces of information. Should be sufficient.",
            'refined_query': None,
            'confidence': 0.8,
            'decision': 'terminate'
        }
    
    async def _calculate_relevance(self, query: str, content: str) -> float:
        """Calcular relevancia simple"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(content_words))
        return min(overlap / len(query_words), 1.0)
    
    async def _generate_next_query(
        self, 
        original: str, 
        docs: List[Dict[str, Any]]
    ) -> str:
        """Generar siguiente query basada en gaps"""
        # Simple: agregar "detailed" o "specific"
        if "detailed" not in original.lower():
            return f"detailed {original}"
        elif "specific" not in original.lower():
            return f"specific examples of {original}"
        else:
            return f"comprehensive analysis of {original}"
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Eliminar resultados duplicados"""
        seen = set()
        unique = []
        
        for result in results:
            # Usar contenido como clave de deduplicación
            content_key = result.get('content', '')[:100]  # Primeros 100 chars
            if content_key not in seen and content_key.strip():
                seen.add(content_key)
                unique.append(result)
        
        return unique
    
    async def _rerank_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Reranking simple por relevancia"""
        scored_results = []
        
        for result in results:
            relevance = await self._calculate_relevance(
                query, result.get('content', '')
            )
            result['relevance_score'] = relevance
            scored_results.append(result)
        
        # Ordenar por relevancia
        return sorted(scored_results, key=lambda x: x['relevance_score'], reverse=True)
    
    def _calculate_total_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calcular confianza total"""
        if not steps:
            return 0.0
        
        confidences = [step.confidence for step in steps]
        return np.mean(confidences)
    
    def _build_reasoning_chain(self, steps: List[ReasoningStep]) -> str:
        """Construir cadena de razonamiento"""
        chain_parts = []
        
        for step in steps:
            part = f"""
Step {step.step_number} ({step.state.value}):
Query: {step.query}
Analysis: {step.analysis}
Confidence: {step.confidence:.2f}
Decision: {step.decision}
Retrieved: {len(step.retrieved_docs)} documents
"""
            chain_parts.append(part.strip())
        
        return "\n\n".join(chain_parts)
    
    async def _synthesize_simple_answer(
        self, 
        query: str, 
        reasoning_chain: str, 
        docs_content: str
    ) -> str:
        """Síntesis simple de respuesta"""
        
        # Respuesta básica basada en el contenido disponible
        if not docs_content.strip():
            return "I couldn't find sufficient information to answer your question."
        
        # Extraer primeros párrafos más relevantes
        sentences = docs_content.split('.')[:5]  # Primeras 5 oraciones
        summary = '. '.join(sentences).strip()
        
        answer = f"""
Based on my analysis of the available information:

{summary}

This answer is based on multiple sources and reasoning steps. The confidence level varies based on the completeness and relevance of the retrieved information.
"""
        
        return answer.strip()
```

---

## 📋 Continuación del Plan de Implementación

El plan continúa con los días 7-12, cubriendo:

### **Día 7**: Sistemas de Memoria (Working, Episodic, Semantic, Procedural)
### **Día 8**: Procesamiento Multimodal (Vision, OCR, Code AST)
### **Día 9**: API Layer con FastAPI, WebSockets, gRPC
### **Día 10**: Real-time Ingestion (IDE tracking, Git hooks, Conversation logging)
### **Día 11**: Testing Suite y Benchmarking vs R2R
### **Día 12**: Optimización M1 Ultra y Deployment

¿Te gustaría que continúe con el plan completo de los días restantes, o prefieres que proceda directamente con la implementación del código ahora que tienes la documentación y planificación base?