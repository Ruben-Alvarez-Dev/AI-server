# Plan maestro: Integración completa VSCode → R2R
Fecha: 2025-08-23
Autor: Cline (asistente automatizado)
Propósito: Diseñar y guardar un plan meticuloso, punto por punto, para capturar y enviar toda la actividad de VSCode (ediciones, hilos/conversaciones, prompts/respuestas de extensiones tipo Cline/Copilot/Continue, commits git, terminales, paneles webview, cambios, etc.) hacia R2R. El plan está particionado en un índice y varias fases y se presenta en formato checklist para ejecución.

--------------------------------------------------------------------------------
ÍNDICE
--------------------------------------------------------------------------------
- 00_Resumen
- 01_Reglas_del_asistente
- 02_Fase_1_Core_Extension
- 03_Fase_2_Sistema_de_Ingesta
- 04_Fase_3_Integraciones_Profundas
- 05_Fase_4_Dashboard_y_Consulta
- 06_Seguridad_Privacidad
- 07_Despliegue_y_Monitorización
- 08_Checklist_Maestra (consolidada)
- 09_Archivos_que_crear / Rutas propuestas

--------------------------------------------------------------------------------
00_Resumen
--------------------------------------------------------------------------------
Objetivo: Tener una solución reproducible y segura que:
- Capture actividad completa del entorno VSCode y extensiones relevantes.
- Envíe eventos a R2R de forma fiable (cola, reintentos, deduplicación).
- Permita consultas, búsqueda semántica y reportes a partir de esa actividad.
- Sea configurable, respetando privacidad y exclusiones.

Alcance de la primera entrega (MVP):
- Extensión VSCode que envía eventos (edits, opens, closes, commits, terminal, debug, visible editors).
- Endpoint en R2R para recibir actividad.
- Worker/queue simple con reintentos.
- Scripts de ingesta existentes adaptados para ingestión segura.
- Documentación y checklist para integración con Cline/Copilot/Continue (hooks donde sea posible).

--------------------------------------------------------------------------------
01_Reglas_del_asistente (las "rules" que me aplico)
--------------------------------------------------------------------------------
1. Lenguaje: Responderé y escribiré documentación en español por defecto.
2. Seguridad de datos:
   - Nunca enviaré contenido de ficheros que contenga secretos (buscar patrones: API_KEY, private_key, password, token) sin que el usuario autorice explícitamente.
   - Excluir directorios configurables (por defecto: .git, node_modules, venv, .venv, /Users/server/Library, /etc).
   - Si un archivo excede el umbral configurable (por defecto 1MB), lo marcaré y pediré instrucciones.
3. Principio de menor privilegio:
   - No ejecutaré instalaciones ni comandos destructivos sin autorización explícita (preguntar antes si requires_approval).
4. Transparencia:
   - Registraré todas las acciones que modifiquen el repositorio o creen ficheros en /plan/logs.txt (metadatos: timestamp, acción, usuario, archivo).
5. Interacción con usuario:
   - Cuando necesite ejecutar comandos en el sistema (ej. docker compose up, pip install), solicitaré permiso si el comando puede afectar el sistema o modificar ficheros.
   - Solicitaré al usuario que active "Act mode" si se requiere operar fuera de la planificación.
6. Versionado:
   - Todas las ediciones de código o archivos planificados se agruparán en una rama `r2r/vscode-activity` y se propondrá un commit con mensaje claro.
7. Pruebas y aceptación:
   - Antes de marcar como completada una tarea, el asistente generará tests/manual steps claros y un checklist de verificación.
8. Conservación de logs:
   - Mantendré un historial de ingestas en `vscode-r2r-activity/cline_activity_all/` (ya existe una carpeta similar). No subiré a servidores remotos sin permiso.
9. Respeto a privacidad local:
   - No enviaré stacktraces ni contenidos sensibles sin anonimizar (opcional: hashes + metadata).
10. Reversibilidad:
   - Todas las acciones se harán con posibilidad de revertir (commits separados, backups).

--------------------------------------------------------------------------------
02_Fase_1_Core_Extension (MVP: extensión VSCode mejorada)
--------------------------------------------------------------------------------
Objetivo: Expandir la extensión `vscode-r2r-activity` para que capture más eventos y ofrezca configuración y tolerancia a fallos.

Tareas (checklist):
- [ ] 2.1 Definir configuración de usuario (`package.json` contributes.configuration):
      - apiUrl (URL R2R)
      - enableActivity (bool)
      - excludedPatterns (array)
      - maxFileSizeBytes (int)
      - redactPatterns (array regex)
- [ ] 2.2 Enviar eventos en batching y con retries:
      - Implementar buffer en memoria y flush periódico (ej: 5s o 100 eventos).
      - Implementar retry/backoff (3 intentos, exponencial).
- [ ] 2.3 Mejorar captura de git:
      - Registrar commits nuevos en tiempo real (git hooks o polling con `git rev-parse HEAD`).
      - Capturar commit hash, autor, message, diff summary (no contenido completo si contiene secretos).
- [ ] 2.4 Capturar actividad de terminal:
      - Opcionalmente registrar comandos ejecutados (si usuario habilita; default: false).
      - Excluir variables de entorno y input interactivo.
- [ ] 2.5 Capturar webviews y outputs:
      - Agregar API para que otras extensiones (o webviews del usuario) puedan invocar `r2r-activity-tracker.wrapCommand` o enviar mensajes.
- [ ] 2.6 Añadir mecanismo de opt-in para extensiones IA:
      - Proveer API simple `sendActivity({type:'conversation', content, source:'cline'})`.
- [ ] 2.7 Implementar modo offline:
      - Guardar eventos en disco (sqllite o JSONL) si R2R no disponible y reintentar después.
- [ ] 2.8 Tests unitarios básicos (Mocha/Jest) para extension:
      - Tests para buffer, retry, exclusiones.
- [ ] 2.9 Documentación de uso y configuración:
      - Actualizar README de `vscode-r2r-activity`.

Precondiciones:
- R2R corriendo localmente (http://localhost:7272).
- Usuario revisa y aprueba `excludedPatterns` y `redactPatterns`.

Criterio de aceptación:
- La extensión envía eventos a R2R, persiste eventos cuando R2R no está y reenvía cuando vuelve a estar online.
- No se envían archivos excluidos ni contenidos con patrones redactados.

--------------------------------------------------------------------------------
03_Fase_2_Sistema_de_Ingesta (back-end R2R)
--------------------------------------------------------------------------------
Objetivo: Crear endpoints y proceso fiable en R2R para recibir, validar, almacenar y buscar actividad.

Tareas (checklist):
- [ ] 3.1 Añadir endpoint `POST /v3/activity` (si no existe) o `POST /v3/vscode-activity`:
      - Validar esquema JSON (tipo, timestamp, source, resource, metadata).
- [ ] 3.2 Validación y normalización:
      - Normalizar rutas (relativas a workspace), extraer repo, branch.
- [ ] 3.3 Queue y worker:
      - Implementar una cola simple (Redis o DB-backed) para procesado asíncrono.
      - Worker que transforma y persiste eventos en la DB (Postgres).
- [ ] 3.4 Indexado para búsqueda:
      - Crear índices para: timestamp, actor, type, file path, commit hash.
- [ ] 3.5 Enriquecimiento:
      - Resolver diffs/summary para commits, extraer entidades (ficheros modificados).
- [ ] 3.6 API de consulta:
      - `GET /v3/activity?offset&limit&type&file&author`
      - `POST /v3/activity/search` (soporte para búsqueda semántica posteriormente).
- [ ] 3.7 Mecanismo de deduplicación:
      - Hash de eventos + ventana temporal para evitar duplicados.
- [ ] 3.8 Tests de integración:
      - End-to-end: extensión -> endpoint -> DB.

Precondiciones:
- Acceso a la instancia R2R (credenciales según configuración del entorno).
- Capacidad de crear tablas / migraciones.

Criterio de aceptación:
- Eventos llegan y son accesibles vía API con latencia aceptable y sin pérdida tras reinicios.

--------------------------------------------------------------------------------
04_Fase_3_Integraciones_Profundas (hooks de extensiones IA)
--------------------------------------------------------------------------------
Objetivo: Capturar conversaciones completas y metadatos de extensiones IA (Cline, Copilot, Continue, MCP tools).

Tareas (checklist):
- [ ] 4.1 Investigar APIs públicas de cada extensión (Cline, Copilot, Continue, etc.)
- [ ] 4.2 Para Cline:
      - [ ] 4.2.1 Integración que captura prompts y respuestas (si Cline expone `globalStorage` o `extension.exports`).
      - [ ] 4.2.2 Monitorizar logs generados por Cline (ruta `Documents/Cline/MCP/...`) y adaptar `monitor_cline_activity.py`.
- [ ] 4.3 Para Copilot:
      - [ ] Detectar paneles o webview outputs si exponibles; si no, capturar sugerencias aplicadas (edits) y su contexto.
- [ ] 4.4 MCP Tools:
      - [ ] Capturar llamadas y respuestas relevantes (si hay hooks).
- [ ] 4.5 Normalizar conversaciones:
      - Estructura: conversation_id, thread_id, role, content, timestamp, attachments, references (file paths).
- [ ] 4.6 Consentimiento y opt-in:
      - Por privacidad, las capturas de conversaciones IA deben requerir opt-in explícito.
- [ ] 4.7 Tests y demos:
      - Pruebas con Cline y otros para verificar captura.

Precondiciones:
- Documentación y permisos de las extensiones a integrar.
- Usuario habilita opt-in para conversaciones IA.

Criterio de aceptación:
- Conversaciones capturadas con hilo y contexto, accesibles en R2R sin filtrar secretos.

--------------------------------------------------------------------------------
05_Fase_4_Dashboard_y_Consulta
--------------------------------------------------------------------------------
Objetivo: Proveer UI para consultar y explorar actividad dentro de VSCode y en la interfaz web de R2R.

Tareas (checklist):
- [ ] 5.1 Panel VSCode (Webview) interactivo:
      - Timeline, filtros (by file, by author, by type), búsqueda rápida.
- [ ] 5.2 Dashboard web en R2R:
      - Página `/activity` con lista, búsqueda semántica básica (later).
- [ ] 5.3 Búsqueda semántica (roadmap):
      - Integrar embeddings (Ollama mxbai-embed-large o motor elegido).
      - Indexado de snippets + metadata.
- [ ] 5.4 Reportes automáticos:
      - Generar resumen diario/por sprint: commits, horas activas, ficheros más cambiados, conversaciones IA.
- [ ] 5.5 Permisos de acceso:
      - Roles: admin, developer, viewer.
- [ ] 5.6 Tests UX:
      - Feedback loop con usuarios (tú) para ajustar visualizaciones.

Precondiciones:
- Endpoints de backend operativos y con datos.
- Modelos de embeddings disponibles si se activa búsqueda semántica.

Criterio de aceptación:
- Panel muestra actividad y filtros, reportes generados correctamente.

--------------------------------------------------------------------------------
06_Seguridad_Privacidad
--------------------------------------------------------------------------------
Puntos clave:
- Excluir ficheros binarios por defecto.
- Detectar y redactor de secrets antes de enviar (patterns configurables).
- Log de auditoría local: `plan/logs.txt`.
- Opciones de anonimización: permitir hash de file paths.
- Si se comparte o publica datos, primero pedir consentimiento.

--------------------------------------------------------------------------------
07_Despliegue_y_Monitorización
--------------------------------------------------------------------------------
Tareas (checklist):
- [ ] 7.1 Crear migraciones DB para tablas de `activity`.
- [ ] 7.2 Añadir configuración en `docker/compose.*.yaml` para servicios adicionales (Redis, worker).
- [ ] 7.3 Añadir healthchecks para endpoint `/v3/activity/health`.
- [ ] 7.4 Monitorización: metrics + logs (Prometheus/Grafana o simple export).
- [ ] 7.5 Backups y retention policy (logs/activity retention).

--------------------------------------------------------------------------------
08_Checklist_Maestra (consolidada)
--------------------------------------------------------------------------------
- [ ] Crear /plan/PLAN.md (este archivo) — completado.
- [ ] Fase 1: Core Extension (ver sección 02)
- [ ] Fase 2: Sistema de ingesta (ver sección 03)
- [ ] Fase 3: Integraciones profundas (ver sección 04)
- [ ] Fase 4: Dashboard y búsqueda (ver sección 05)
- [ ] Seguridad y privacidad (ver sección 06)
- [ ] Despliegue y monitorización (ver sección 07)
- [ ] Revisiones y pruebas de aceptación
- [ ] Merge a rama `r2r/vscode-activity` y PR

--------------------------------------------------------------------------------
09_Archivos_que_crear / Rutas propuestas
--------------------------------------------------------------------------------
- plan/PLAN.md  (este archivo)
- plan/logs.txt  (registro de acciones del asistente)
- vscode-r2r-activity/src/ (actualizar extension.ts y añadir buffer/retry)
- vscode-r2r-activity/package.json (contributes.configuration)
- vscode-r2r-activity/src/test/ (tests)
- R2R/py/r2r/ (añadir endpoint / procesamiento de activity)
- R2R/deployment/ (actualizar docker compose con worker y optional redis)
- vscode-r2r-activity/scripts/ (monitor_cline_activity.py, ingest_cline_safe.py adaptados)
- docs/vscode-integration.md (guía de instalación y opt-in)

--------------------------------------------------------------------------------
Logs / seguimiento (inmediato)
--------------------------------------------------------------------------------
- [x] He creado el plan maestro como `plan/PLAN.md` con índice y fases (este archivo).
- Próximo paso: ¿quieres que empiece a:
  1) Actualizar la extensión `vscode-r2r-activity` para implementar buffer/retry y polling git? (requiere tocar `vscode-r2r-activity/src/extension.ts`)  
  2) O prefieres que primero cree el endpoint en R2R para recibir actividad?

Indica la opción y procederé. Si autorizas cambios en código y commits, dime también si debo crear una rama `r2r/vscode-activity` y commitear los cambios (requieres_approval para commits integrales: false — los cambios serán creados en archivos y te pediré confirmación para commitear).
