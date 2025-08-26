# Model Watcher - AI-Server

Servicio automático que organiza modelos de `/models/` en una estructura categorizada en `/models/pool/` usando **copias físicas reales**.

## 🎯 Concepto

- **`/models/`**: Tu zona de pruebas - tira aquí cualquier modelo, borra cuando quieras
- **`/models/pool/`**: Copias físicas organizadas (modelos en servicio)
- **Apps usan `/models/pool/`**: Nunca referencias directas a `/models/`
- **`/models/README.md`**: Lista automática de qué app usa qué modelo

## 📁 Estructura Automática

```
models/
├── [tus modelos aquí]              # Zona de dump
├── pool/                           # Auto-organizado
│   ├── llm/
│   │   ├── code/                  # deepseek-coder, codellama
│   │   ├── chat/                  # llama-chat, mistral-instruct  
│   │   ├── general/               # llama, mistral, mixtral
│   │   └── specialized/           # summary, translate, etc
│   ├── embedding/                 # sentence-transformers, BGE, E5
│   ├── multimodal/               # LLaVA, CLIP, vision models
│   └── uncategorized/            # No clasificados
└── .model_registry.json          # Registro automático
```

## 🚀 Uso

### Inicio Manual
```bash
cd tools/model-watcher
python watcher.py
```

### Inicio Automático con AI-Server
```python
# En tu script de inicio de AI-Server
from tools.model_watcher.auto_start import start_watcher_background
start_watcher_background()
```

### Como Servicio Systemd (Linux)
```bash
sudo cp model-watcher.service /etc/systemd/system/
sudo systemctl enable model-watcher
sudo systemctl start model-watcher
```

## 🏷️ Clasificación Automática

El watcher clasifica modelos por:

1. **Nombre**: Detecta keywords
   - `*coder*`, `*code*` → `llm/code/`
   - `*chat*`, `*instruct*` → `llm/chat/`
   - `*embed*`, `*e5*`, `*bge*` → `embedding/`
   - `*llava*`, `*vision*` → `multimodal/`

2. **Tamaño**: Heurística
   - `> 5GB` → Probablemente LLM
   - `< 1GB` → Probablemente embedding

3. **Extensión**: `.gguf`, `.bin`, `.safetensors`, etc.

## 🔄 Workflow

1. **Bajas modelo** en `/models/`:
   ```bash
   wget https://modelo.gguf -P models/
   ```

2. **Watcher detecta** y copia al pool:
   ```
   📋 Copying deepseek-coder.gguf to pool (6.7 GB)...
   ✅ Copied: models/deepseek-coder.gguf -> models/pool/llm/code/deepseek-coder.gguf
   ```

3. **Apps usan** el pool organizado:
   ```python
   model_path = "models/pool/llm/code/deepseek-coder.gguf"
   ```

4. **Puedes vaciar** `/models/` cuando quieras:
   - Las copias en pool siguen funcionando
   - El README.md mantiene el tracking de uso

## 📊 Registry

El archivo `.model_registry.json` mantiene:
```json
{
  "models": {
    "hash123": {
      "source": "models/deepseek-coder.gguf",
      "pool_path": "models/pool/llm/code/deepseek-coder.gguf",
      "category": "llm/code",
      "size": 7340032000,
      "created": "2024-03-20T10:30:00",
      "used_by": ["llm-server", "open-interpreter"]
    }
  }
}
```

El archivo `README.md` auto-generado muestra:
- **MODELOS SIN USO** (arriba de todo)
- **MODELOS POR APLICACIÓN** (organizados por app)

## 🛠️ Configuración

En `watcher.py` puedes ajustar:
- Categorías y keywords de clasificación
- Intervalo de escaneo (default: 30s)
- Extensiones de modelo reconocidas
- Tamaño mínimo para considerar archivo como modelo

## 💡 Tips

- **No toques `/pool/`**: Son las copias en servicio
- **Borra desde `/models/`**: El pool sigue intacto
- **Check `/models/README.md`**: Ver qué usa cada app
- **Logs**: Check output para ver clasificaciones

## 🔧 Troubleshooting

- **Espacio en disco**: Las copias duplican espacio (eso es lo que queremos)
- **Clasificación incorrecta**: Ajusta keywords en `classification_rules`
- **No detecta modelo**: Verifica extensión o tamaño mínimo
- **Copia lenta**: Normal para modelos grandes (muestra progreso)