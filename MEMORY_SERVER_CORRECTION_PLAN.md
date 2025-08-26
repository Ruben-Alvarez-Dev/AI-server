# 🚨 Plan de Corrección Memory-Server
**Fecha:** 2025-08-26  
**Prioridad:** CRÍTICA

## 📋 Resumen Ejecutivo
Se han identificado 3 desfases críticos entre el diseño original y la implementación actual del Memory-Server que causan problemas de saturación y rendimiento.

## 🔴 Problemas Críticos Identificados

### 1. Embedding Hub Centralizado (Arquitectura Incorrecta)
- **Estado Actual:** Cliente conecta a hub centralizado (puerto 8900)
- **Diseño Correcto:** Endpoints dedicados para cada tipo de embedding
- **Impacto:** Cuello de botella, punto único de falla

### 2. Ingesta Síncrona y Bloqueante
- **Estado Actual:** Usa `BackgroundTasks` de FastAPI (pseudo-asíncrono)
- **Diseño Correcto:** Sistema de colas con workers dedicados
- **Impacto:** Saturación del servidor, timeouts, mala experiencia

### 3. Ausencia de Sistema de Colas
- **Estado Actual:** Sin RabbitMQ/Redis/Celery
- **Diseño Correcto:** Colas distribuidas con workers
- **Impacto:** No escalable, sin tolerancia a fallos

## ✅ Plan de Corrección (5 Días)

### Día 1: Implementar Sistema de Colas con Redis
```python
# requirements.txt additions
redis==5.0.1
celery==5.3.4
flower==2.0.1  # Para monitoreo
```

**Tareas:**
1. Instalar y configurar Redis localmente
2. Configurar Celery con Redis como broker
3. Crear workers para procesamiento de documentos
4. Migrar ingesta a tareas Celery

### Día 2: Refactorizar Arquitectura de Embeddings
**Eliminar el hub centralizado y crear servicios independientes:**

```python
# Nuevo diseño: servicios independientes
services/
├── embedding-late-chunking/    # Puerto 8901
├── embedding-code/              # Puerto 8902  
├── embedding-conversation/      # Puerto 8903
├── embedding-visual/            # Puerto 8904
├── embedding-query/             # Puerto 8905
└── embedding-community/         # Puerto 8906
```

### Día 3: Implementar Nuevo Cliente de Embeddings
```python
# core/embedding_services.py (NUEVO)
class EmbeddingServices:
    """Cliente para servicios de embeddings especializados"""
    
    def __init__(self):
        self.services = {
            'late_chunking': 'http://localhost:8901',
            'code': 'http://localhost:8902',
            'conversation': 'http://localhost:8903',
            'visual': 'http://localhost:8904',
            'query': 'http://localhost:8905',
            'community': 'http://localhost:8906'
        }
    
    async def get_embedding(self, content: str, service_type: str):
        """Obtener embedding del servicio específico"""
        service_url = self.services[service_type]
        # Llamada directa al servicio especializado
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{service_url}/embed", 
                                   json={"content": content}) as response:
                return await response.json()
```

### Día 4: Migrar Endpoints de Ingesta
```python
# api/routers/documents.py (ACTUALIZADO)
from celery import current_app

@router.post("/upload")
async def upload_document(file: UploadFile):
    """Upload con procesamiento asíncrono real"""
    
    # 1. Guardar archivo temporalmente
    temp_path = await save_temp_file(file)
    
    # 2. Crear tarea Celery (NO bloquea)
    task = current_app.send_task(
        'process_document',
        args=[temp_path, file.filename]
    )
    
    # 3. Respuesta inmediata
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Document queued for processing"
    }

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Check processing status"""
    task = current_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

### Día 5: Testing y Optimización
1. **Tests de carga** con múltiples archivos simultáneos
2. **Monitoreo** con Flower para Celery
3. **Métricas** de rendimiento
4. **Documentación** actualizada

## 🔧 Implementación Inmediata (HOY)

### Paso 1: Instalar Redis
```bash
# macOS
brew install redis
brew services start redis

# Verificar
redis-cli ping  # Debe responder PONG
```

### Paso 2: Configurar Celery
```python
# apps/memory-server/core/celery_app.py
from celery import Celery
from core.config import get_config

config = get_config()

celery_app = Celery(
    'memory_server',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos max
    task_soft_time_limit=240,  # Warning a los 4 minutos
)
```

### Paso 3: Crear Worker de Ingesta
```python
# apps/memory-server/workers/document_worker.py
from celery import Task
from core.celery_app import celery_app
from api.utils.document_processor import DocumentProcessor

class DocumentIngestionTask(Task):
    """Task con inicialización única"""
    _processor = None
    
    @property
    def processor(self):
        if self._processor is None:
            self._processor = DocumentProcessor()
        return self._processor

@celery_app.task(base=DocumentIngestionTask, bind=True)
def process_document(self, file_path: str, original_name: str, **kwargs):
    """Procesar documento en background"""
    try:
        # Update task state
        self.update_state(state='PROCESSING', 
                         meta={'current': 'Analyzing document'})
        
        # Process document
        doc_id = self.processor.process_file(
            file_path=file_path,
            original_name=original_name,
            **kwargs
        )
        
        return {
            'status': 'success',
            'document_id': doc_id,
            'message': f'Document {original_name} processed successfully'
        }
        
    except Exception as e:
        # Log error
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
```

### Paso 4: Iniciar Workers
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
cd apps/memory-server
celery -A core.celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Flower (Monitoreo)
celery -A core.celery_app flower --port=5555

# Terminal 4: Memory Server
python -m uvicorn api.main:app --reload --port=8001
```

## 📊 Métricas de Éxito

### Antes (Actual)
- ❌ Timeout con >3 archivos simultáneos
- ❌ Worker bloqueado durante ingesta
- ❌ Sin visibilidad del progreso
- ❌ Un punto de falla (embedding-hub)

### Después (Objetivo)
- ✅ 100+ archivos simultáneos sin timeout
- ✅ Workers dedicados no bloquean API
- ✅ Progress tracking con task_id
- ✅ Servicios independientes resilientes
- ✅ Escalable horizontalmente

## 🚀 Comandos de Implementación

```bash
# 1. Instalar dependencias
cd apps/memory-server
pip install redis celery flower aioredis

# 2. Crear estructura de workers
mkdir -p workers
touch workers/__init__.py
touch workers/document_worker.py
touch workers/embedding_worker.py

# 3. Actualizar configuración
echo "REDIS_URL=redis://localhost:6379" >> .env
echo "CELERY_BROKER_URL=redis://localhost:6379/0" >> .env
echo "CELERY_RESULT_BACKEND=redis://localhost:6379/1" >> .env

# 4. Test básico
python -c "from celery import Celery; app = Celery('test', broker='redis://localhost:6379'); print('✅ Celery conectado a Redis')"
```

## 🎯 Prioridades

1. **CRÍTICO:** Sistema de colas con Redis/Celery (Día 1)
2. **ALTO:** Refactorizar endpoints de ingesta (Día 2)  
3. **MEDIO:** Separar servicios de embeddings (Día 3-4)
4. **BAJO:** Optimización y monitoreo (Día 5)

## 📝 Notas Importantes

- La implementación debe ser **incremental** para no romper el sistema actual
- Mantener **compatibilidad hacia atrás** durante la transición
- Implementar **feature flags** para activar/desactivar nuevas características
- Documentar **todos los cambios** en el código

## 🔄 Siguiente Paso Inmediato

**EJECUTAR AHORA:**
```bash
# Instalar Redis y verificar
brew install redis
redis-server --daemonize yes
redis-cli ping

# Si responde "PONG", proceder con Paso 2
```

---

**Autor:** Rubén Álvarez  
**Estado:** PENDIENTE DE IMPLEMENTACIÓN