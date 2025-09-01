# 🌐 Reglas de Idioma y Comunicación

## 🗣️ Idioma de Comunicación
- **Habla siempre en español** para toda la comunicación con el usuario
- Mantén un tono profesional pero cercano
- Explica conceptos técnicos de manera clara y accesible
- Documentación de usuario siempre en español

## 💻 Idioma de Código
- **Todo el código debe estar en inglés**: variables, funciones, clases, comentarios
- Los comentarios deben ser claros y descriptivos en inglés
- La documentación técnica debe estar en inglés
- Los mensajes de commit deben estar en inglés
- Logs de sistema en inglés

## 🏴‍☠️ ATLAS Black Box Integration
- **ATLAS es CAJA NEGRA**: Solo se documenta su interface pública
- **NO documentar internals**: Funcionamiento interno es completamente opaco
- **Nomenclatura ATLAS**: Prefijo `atlas_` para todas las interfaces públicas
- **Comentarios ATLAS**: Solo sobre integración y uso, jamás sobre internals
- **Documentación ATLAS**: Solo endpoints, schemas y ejemplos de uso

## 📝 Convenciones de Nomenclatura

### Variables y Funciones
- **Variables**: `camelCase` (ej: `userProfile`, `isLoading`, `atlasClient`)
- **Funciones**: `camelCase` (ej: `calculateTotal`, `validateInput`, `atlas_process`)
- **Funciones ATLAS**: `atlas_` prefix (ej: `atlas_enhance`, `atlas_query`)

### Clases y Tipos
- **Clases**: `PascalCase` (ej: `UserService`, `DatabaseConnection`, `AtlasConnector`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej: `MAX_RETRIES`, `API_TIMEOUT`, `ATLAS_ENDPOINT`)
- **Interfaces**: `PascalCase` con prefijo `I` (ej: `IUserData`, `IResponse`, `IAtlasConfig`)
- **Tipos**: `PascalCase` con sufijo `Type` (ej: `UserType`, `StatusType`, `AtlasRequestType`)

### ATLAS Específico
- **Interfaces públicas**: `Atlas` prefix (ej: `AtlasClient`, `AtlasRequest`, `AtlasResponse`)
- **Configuración**: `atlas_` prefix (ej: `atlas_url`, `atlas_timeout`)
- **Endpoints**: `/atlas/v1/` pattern
- **Archivos**: `atlas_` prefix para interfaces (ej: `atlas_connector.py`, `atlas_client.js`)

## 🎨 Metodología BEM (CSS)

- **Block**: Componente principal (ej: `.header`, `.menu`, `.atlas-panel`)
- **Element**: Partes del bloque (ej: `.header__logo`, `.menu__item`, `.atlas-panel__status`)
- **Modifier**: Variaciones (ej: `.header--fixed`, `.menu__item--active`, `.atlas-panel--loading`)
- **Guiones dobles** para modificadores: `--`
- **Guiones bajos dobles** para elementos: `__`
- **Mantener la especificidad baja**
- **ATLAS components**: `.atlas-` prefix para componentes ATLAS

## 🧩 Componentización

- **Crear componentes reutilizables** siempre que sea posible
- **Separar responsabilidades** claramente
- **Mantener componentes pequeños** y enfocados
- **Usar composición** sobre herencia
- **Implementar props/interfaces** bien definidas
- **ATLAS integration**: Cada componente debe considerar integración ATLAS donde aplique
- **Interface-first design**: Definir interfaces públicas antes de implementación

## ✅ Clean Code Principles

- **DRY** (Don't Repeat Yourself): Evitar duplicación de código
- **KISS** (Keep It Simple, Stupid): Simplicidad ante todo
- **YAGNI** (You Aren't Gonna Need It): No añadir funcionalidad innecesaria
- **SOLID** principles aplicados apropiadamente
- **Single Responsibility**: Cada componente/función una sola responsabilidad
- **Black Box Compliance**: ATLAS internals nunca expuestos

## 📋 Ejemplos Prácticos

### ✅ Correcto

```typescript
// English comments for technical code
interface IAtlasConfig {
  endpoint: string;
  timeout: number;
  apiKey: string;
}

interface IUserProfile {
  firstName: string;
  lastName: string;
  email: string;
}

function calculateUserScore(userData: IUserProfile): number {
  // Calculate user engagement score
  return score;
}

// ATLAS integration - public interface only
async function atlas_enhanceContent(content: string): Promise<string> {
  // Use ATLAS public API to enhance content
  const response = await atlasClient.process({
    input: content,
    mode: 'enhance'
  });
  return response.result;
}

// CSS with BEM + ATLAS
.header {}
.header__logo {}
.header--fixed {}
.atlas-panel {}
.atlas-panel__status {}
.atlas-panel--loading {}
```

### ❌ Incorrecto  

```typescript
// Spanish comments in code (should be English)
interface PerfilUsuario { // Spanish names
  nombre: string;
  apellido: string;
  correo: string;
}

function calcularPuntuacion(datosUsuario: PerfilUsuario): number {
  // Mixed language
  return puntuacion;
}

// ATLAS internal exposure (PROHIBITED)
function atlas_internal_algorithm(data: any): any {
  // NEVER document or expose ATLAS internals
  const internalState = atlas_private_function();
  return processInternally(internalState);
}

// CSS without methodology
.header {}
.logo {}
.fixed-header {}
.atlas_stuff {} // Inconsistent naming
```

## 🔄 Flujo de Trabajo Comunicación

1. **Analizar requisitos** en español con el usuario
2. **Implementar código** en inglés siguiendo convenciones
3. **Documentar técnicamente** en inglés
4. **Integrar ATLAS** usando solo interfaces públicas
5. **Comunicar resultados** en español al usuario
6. **Revisar que se cumplan** todas las convenciones
7. **Logs técnicos** en inglés, logs de progreso pueden ser en español

## 🚨 Validaciones Automáticas

- **Pre-commit hooks** verifican nomenclatura
- **Linting rules** para consistencia de idioma
- **ATLAS compliance** check para evitar exposición de internals
- **BEM validation** en CSS
- **Comment language** validation (inglés en código técnico)

---

**📝 Nota**: Estas reglas aseguran comunicación clara con usuarios en español mientras mantenemos código técnico profesional en inglés, con integración ATLAS como caja negra.