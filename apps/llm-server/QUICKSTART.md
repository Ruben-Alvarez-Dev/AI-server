# LLM Server - Inicio Rápido 🚀

## Comando de Inicio Único

Para arrancar el servidor completo con **un solo comando**:

```bash
./start.sh
```

¡Eso es todo! El servidor se iniciará automáticamente y mostrará:
- ✅ URLs de conexión
- ✅ API Key para compatibilidad OpenAI
- ✅ Ejemplos de comandos curl
- ✅ Estado del modelo y rendimiento

## Lo que hace automáticamente:

1. **Verifica dependencias** (Python, venv, paquetes)
2. **Chequea modelos** (confirma que estén en su lugar)
3. **Configura el entorno** (128K contexto, Metal acceleration)
4. **Inicia el servidor** con banners informativos
5. **Muestra URLs y API Key** para conexión inmediata

## Información de Conexión:

- **API Principal**: http://localhost:8000
- **OpenAI Compatible**: http://localhost:8000/v1/chat/completions  
- **API Key**: `sk-llmserver-local-development-key-12345678`
- **Documentación**: http://localhost:8000/docs

## Pruebas Rápidas:

```bash
# Prueba matemática con razonamiento
curl -X POST http://localhost:8000/test/math

# Generación de código
curl -X POST http://localhost:8000/test/coding

# Modo planificación
curl -X POST http://localhost:8000/test/plan-mode
```

## OpenAI API Example:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-llmserver-local-development-key-12345678" \
  -d '{"model":"qwen2.5-coder-7b","messages":[{"role":"user","content":"Hello AI!"}]}'
```

## Características:

- 🧠 **128K tokens** de contexto
- ⚡ **55+ tokens/segundo** en M1 Ultra
- 🎯 **6 modos**: Chat, Plan, Act, Agent, Edit, Continue
- 🔄 **Streaming** soportado
- 🤖 **OpenAI compatible** 100%
- 🚀 **Metal acceleration** activada

Para detener el servidor: **Ctrl+C**