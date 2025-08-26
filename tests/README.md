# Testing Framework - AI-Server

## Estructura de Testing

```
tests/
├── README.md                 # Este archivo - documentación completa
├── conftest.py              # Configuración global pytest
├── test_config.py           # Configuración específica de tests
├── requirements.txt         # Dependencias para testing
├── run_tests.py            # Script principal de ejecución
├── unit/                   # Tests unitarios
│   ├── __init__.py
│   ├── test_startup_script.py
│   ├── test_memory_server.py
│   ├── test_llm_server.py
│   └── test_model_watcher.py
├── integration/            # Tests de integración
│   ├── __init__.py
│   ├── test_server_communication.py
│   ├── test_api_endpoints.py
│   └── test_service_orchestration.py
├── functional/             # Tests funcionales end-to-end
│   ├── __init__.py
│   ├── test_complete_workflow.py
│   ├── test_memory_operations.py
│   └── test_llm_operations.py
├── fixtures/               # Datos de prueba
│   ├── __init__.py
│   ├── test_documents/
│   ├── test_models/
│   └── mock_responses/
├── logs/                   # Logs específicos de testing
│   ├── test_execution.log
│   ├── component_tests.log
│   ├── integration_tests.log
│   └── performance_tests.log
└── reports/                # Reportes de testing
    ├── coverage/
    ├── performance/
    └── test_results.json
```

## Metodología de Testing

### 1. Tests Unitarios
- Cada componente individual
- Mocking de dependencias externas
- Cobertura > 80%

### 2. Tests de Integración  
- Comunicación entre servicios
- APIs y endpoints
- Flujo de datos

### 3. Tests Funcionales
- Escenarios completos de usuario
- End-to-end workflows
- Validación de funcionalidad real

### 4. Logging y Reportes
- Logs detallados por categoría
- Métricas de rendimiento
- Reportes de cobertura
- Resultados estructurados JSON

## Ejecución

```bash
# Tests completos
python tests/run_tests.py --all

# Por categoría
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --functional

# Componente específico
python tests/run_tests.py --component memory-server
```

## Configuración

- `conftest.py`: Fixtures globales, configuración pytest
- `test_config.py`: Variables de entorno, paths, configuración
- Logs rotables y estructurados
- Cleanup automático después de tests