# 🔌 AI-Server Port Allocation Plan
**Rango Total:** 8000-8999

## 📊 Estructura Jerárquica por Importancia

### 🎯 Core Services (8000-8099) - CRÍTICOS
```
8001 - Memory-Server API (Principal)
8002 - Memory-Server WebSockets
8003 - Memory-Server gRPC
8010 - LLM-Server API (Principal)
8011 - LLM-Server WebSockets
8020 - Main Router/Gateway (si se implementa)
```

### 🧠 LLM & Embedding Services (8100-8199) - ALTA PRIORIDAD
```
8100 - Desarrollo/Testing
8900 - Embedding-Hub Central (ACTIVO - centralizado con agentes internos)
8111 - Embedding Late-Chunking (RESERVADO - backup futuro)
8112 - Embedding Code (RESERVADO - backup futuro)
8113 - Embedding Conversation (RESERVADO - backup futuro)  
8114 - Embedding Visual (RESERVADO - backup futuro)
8115 - Embedding Query (RESERVADO - backup futuro)
8116 - Embedding Community (RESERVADO - backup futuro)
```

### 🔄 Processing & Queue Services (8800-8899) - SOPORTE CRÍTICO
```
8801 - Redis (Memory-Server queues)
8802 - Redis (LLM-Server queues) 
8803 - RabbitMQ Management (si se usa)
8804 - RabbitMQ AMQP (si se usa)
8811 - Celery Flower (Memory-Server monitoring)
8812 - Celery Flower (LLM-Server monitoring)
```

### 📊 Monitoring & Support (8900-8999) - SOPORTE
```
8900 - Prometheus Metrics
8901 - Grafana Dashboard
8910 - Service Registry/Discovery
8920 - Health Check Aggregator
```

### 📁 Storage & Data (8200-8299) - DATOS
```
8200 - Vector Database (FAISS API)
8201 - Graph Database (Neo4j)
8202 - Document Storage API
8210 - Backup Services
```

### 🔧 Development & Tools (8300-8399) - DESARROLLO
```
8300 - Hot Reload Dev Server
8301 - Testing Framework
8302 - Debug Services
8310 - Code Analysis Tools
```

## 🚀 Implementación Inmediata

Para el sistema de colas que estamos implementando:

```
8801 - Redis (Memory-Server)
8810 - Flower Monitoring (Memory-Server)
```

### Configuración de Redis
```bash
# Config personalizado para AI-Server
port 8801
bind 127.0.0.1
```

### Configuración de Flower
```bash
# Flower en puerto dedicado
flower --port=8810 --broker=redis://localhost:8801/0
```

## 📝 Ventajas de esta Estructura

1. **Separación Clara:** Core services en 8000s, soporte en 8800s
2. **Escalabilidad:** Rangos dedicados para cada tipo de servicio  
3. **Debugging:** Fácil identificar qué servicio por puerto
4. **Jerarquía:** Puertos bajos = más críticos
5. **Expansión:** Espacio para crecer en cada categoría
6. **Hardware Optimizado:** M1 Ultra 128GB puede manejar cualquier configuración

## ✅ Estado Actual (Implementado)

1. **✅ Completado:** Redis en 8801, Flower en 8810
2. **✅ Completado:** Sistema de colas asíncrono funcionando
3. **✅ Completado:** Hub centralizado en 8900 (agenttic interno)
4. **✅ Reservado:** Puertos 8111-8116 para futura expansión especializada

## 🎯 Estrategia de Embeddings

- **Activo:** Hub centralizado (8900) con lógica agenttic interna
- **Reservado:** Servicios especializados (8111-8116) para escalabilidad futura
- **Flexibilidad:** Puede migrar fácilmente entre estrategias según necesidad