# Memory Server - Guía de Testing desde VSCode

## 🚀 Formas de Probar el Memory Server desde VSCode

### 1️⃣ **REST Client Extension (Recomendado)**

#### Instalación:
```bash
# En VSCode Command Palette (Cmd+Shift+P):
ext install humao.rest-client
```

#### Uso:
1. Abre el archivo `memory-server-api-tests.http` 
2. Haz clic en **"Send Request"** sobre cualquier endpoint
3. Ve las respuestas en el panel derecho

**Endpoints disponibles**:
- ✅ Health checks
- ✅ System info  
- ✅ Document management
- ✅ Search functionality
- ✅ Summarization
- ✅ Web search

### 2️⃣ **VSCode Tasks (Automatizado)**

#### Uso:
1. **Command Palette** → `Tasks: Run Task`
2. Selecciona una tarea:

**Tareas Disponibles**:
- `Memory Server: Start` - Iniciar servidor
- `Memory Server: Stop` - Detener servidor  
- `Memory Server: Test Health` - Check rápido
- `Memory Server: Run All Tests` - Tests completos
- `Memory Server: Open Swagger Docs` - Abrir documentación
- `Memory Server: View Logs` - Ver logs en tiempo real

#### Atajos de Teclado:
- `Ctrl+Shift+P` → `Tasks: Run Task` → Seleccionar

### 3️⃣ **Debug & Launch (Desarrollo)**

#### Debug del Servidor:
1. **Run and Debug** panel (Ctrl+Shift+D)
2. Selecciona **"Debug Memory Server"**
3. Presiona F5 para debug con breakpoints

#### Debug de Tests:
1. Selecciona **"Run Memory Server Tests"**  
2. F5 para ejecutar tests con debug

### 4️⃣ **Terminal Interactivo**

#### Herramienta Interactiva:
```bash
# En VSCode Terminal:
python test_memory_server_interactive.py

# O modo automático:
python test_memory_server_interactive.py --auto
```

**Menú Interactivo**:
```
1. Health Check
2. System Information  
3. List Workspaces
4. Document Statistics
5. Create Test Document
6. Search Documents
7. Web Search Test
8. Content Summarization
9. Log Activity
10. Run All Tests
```

### 5️⃣ **Python Testing Integration**

#### Unit Tests:
1. **Testing panel** en VSCode
2. Ve tests en `tests/memory-server-tests/`
3. Ejecuta tests individuales con clic

#### Comandos de Terminal:
```bash
# Tests unitarios
cd tests/memory-server-tests
python -m pytest unit/ -v

# Tests específicos  
python -m pytest unit/test_config.py -v

# Tests de funcionalidad real
python test_actual_functionality.py
```

---

## 📋 Paso a Paso - Primera Prueba

### 1. **Verificar que el servidor esté corriendo**
```bash
# En terminal VSCode:
curl http://127.0.0.1:8001/health/
```
**Respuesta esperada**: `{"status":"healthy",...}`

### 2. **Usar REST Client** 
1. Abre `memory-server-api-tests.http`
2. Haz clic en "Send Request" en la primera línea:
```http
GET {{baseUrl}}/health/
```
3. Ve la respuesta JSON a la derecha

### 3. **Probar Documentación Interactive**
1. Command Palette → `Tasks: Run Task`
2. Selecciona `Memory Server: Open Swagger Docs`
3. Se abre http://127.0.0.1:8001/docs en tu navegador

### 4. **Crear un documento de prueba**
En `memory-server-api-tests.http`, busca:
```http
### 13. Create Workspace Document
POST {{baseUrl}}/api/v1/documents/workspace/test
```
Haz clic en "Send Request"

### 5. **Ejecutar pruebas completas**
```bash
# Terminal VSCode:
python test_memory_server_interactive.py --auto
```

---

## 🔧 Configuración de VSCode

### Extensions Recomendadas:
- ✅ **REST Client** (humao.rest-client) - Para API testing
- ✅ **Python** (ms-python.python) - Para desarrollo Python  
- ✅ **Python Debugger** (ms-python.debugpy) - Para debugging
- ✅ **Thunder Client** (rangav.vscode-thunder-client) - Alternativa REST
- ✅ **JSON** (vscode.json-language-features) - Para responses

### Settings configurados:
- Python interpreter: `./apps/memory-server/venv/bin/python`
- Test framework: pytest
- Linting: flake8
- Formatting: black

---

## 🌐 URLs Importantes

Mientras el servidor esté corriendo en puerto 8001:

- **API Base**: http://127.0.0.1:8001/
- **Swagger Docs**: http://127.0.0.1:8001/docs  
- **Health**: http://127.0.0.1:8001/health/
- **OpenAPI Schema**: http://127.0.0.1:8001/openapi.json

---

## 🧪 Ejemplos de Testing

### Ejemplo 1: Health Check
```http
GET http://127.0.0.1:8001/health/
Accept: application/json
```

### Ejemplo 2: Crear Documento
```http
POST http://127.0.0.1:8001/api/v1/documents/workspace/test
Content-Type: application/json

{
    "title": "Mi Documento de Prueba",
    "content": "Este es contenido de prueba desde VSCode",
    "metadata": {
        "source": "vscode",
        "tags": ["test", "vscode"]
    }
}
```

### Ejemplo 3: Búsqueda Web
```http
POST http://127.0.0.1:8001/api/v1/search/web
Content-Type: application/json

{
    "query": "Python machine learning", 
    "max_results": 3
}
```

---

## 🐛 Troubleshooting

### Server no responde:
```bash
# Verificar si está corriendo:
curl http://127.0.0.1:8001/health/

# Si no responde, iniciarlo:
cd apps/memory-server
venv/bin/uvicorn api.main:app --port 8001
```

### Tests fallan:
```bash
# Verificar Python path:
export PYTHONPATH=/Users/server/AI-projects/AI-server/apps/memory-server

# Ejecutar test individual:
cd tests/memory-server-tests
python test_actual_functionality.py
```

### Extension REST Client:
1. Instalar: `ext install humao.rest-client`
2. Reiniciar VSCode
3. Abrir archivo `.http`

---

## ⚡ Atajos Rápidos

### Teclado:
- `F5` - Start debugging
- `Ctrl+Shift+P` - Command palette
- `Ctrl+` ` - Toggle terminal
- `Ctrl+Shift+D` - Debug panel
- `Ctrl+Shift+E` - Explorer panel

### Testing Rápido:
```bash
# Health check rápido:
curl -s http://127.0.0.1:8001/health/ | python -m json.tool

# Info del sistema:
curl -s http://127.0.0.1:8001/ | python -m json.tool

# Ver workspaces:
curl -s http://127.0.0.1:8001/api/v1/documents/workspaces | python -m json.tool
```

---

¡El Memory Server está listo para testing desde VSCode! 🎉

Utiliza cualquiera de estos métodos según tu preferencia:
- **REST Client** para testing interactivo de APIs
- **Tasks** para operaciones automatizadas  
- **Debug** para desarrollo con breakpoints
- **Terminal** para comandos directos
- **Testing Panel** para unit tests