# ADR-001: Directory Structure Architecture

**Status**: ✅ Accepted  
**Date**: 2024-08-25  
**Authors**: AI-Server Team  
**Reviewers**: Project Lead  

## Context and Problem Statement

The AI-Server project began as a collection of services and tools that grew organically. As the system expanded to include multiple applications (LLM Server, Memory Server), services (Model Watcher), and development tools (CLI interfaces, VS Code extensions), the original flat structure became difficult to navigate and maintain.

**Problems with previous structure:**
- No clear separation between applications, services, and development tools
- Duplicated directories and inconsistent naming (`web-scraper` vs `web-scrapper`)
- Mixed concerns (scripts, source code, and deployment configs in the same level)
- Difficult onboarding for new developers
- Scaling challenges for future microservices architecture

## Decision Drivers

1. **Scalability**: Need to accommodate future growth (more apps, services, models)
2. **Team Separation**: Different teams will own different parts of the system
3. **Deployment Independence**: Each app/service should be deployable independently
4. **Developer Experience**: Clear navigation and understanding of codebase
5. **Industry Standards**: Follow proven patterns from successful large-scale projects
6. **CI/CD Readiness**: Structure that supports automated build and deployment

## Considered Options

### Option 1: Deep Nested Structure
```
AI-server/
├── src/
│   ├── apps/
│   │   ├── llm-server/
│   │   └── memory-server/
│   ├── services/
│   └── tools/
```

**Pros**: Traditional software project structure  
**Cons**: Long import paths, complex navigation, unclear executable locations

### Option 2: Monorepo Flat Structure  
```
AI-server/
├── llm-server/
├── memory-server/  
├── model-watcher/
├── cli-tools/
```

**Pros**: Simple, flat structure  
**Cons**: No conceptual grouping, doesn't scale with growth

### Option 3: Enterprise Multi-App Architecture (CHOSEN)
```
AI-server/
├── apps/           # User-facing applications
├── services/       # Background services  
├── tools/          # Development tooling
├── bin/            # Executable scripts
├── src/            # Shared source code
├── assets/         # Static resources (models, prompts)
├── config/         # Environment configurations
```

## Decision

We chose **Option 3: Enterprise Multi-App Architecture** because:

### Conceptual Clarity
- **apps/**: Things end users interact with directly (LLM Server API, Dashboard)
- **services/**: Background services that support apps (Model Watcher, Vector DB)  
- **tools/**: Developer-facing utilities (CLI, VS Code extension, scrapers)
- **bin/**: Executable scripts and commands
- **src/**: Shared libraries and common code
- **assets/**: Static resources organized by type

### Industry Alignment

This pattern is used by major tech companies and successful open-source projects:

**Microsoft (.NET, Azure Services)**:
```
├── src/            # Source code
├── apps/           # Applications  
├── services/       # Background services
├── tools/          # Tooling
```

**Google (Kubernetes, Go projects)**:
```
├── cmd/            # Commands (our bin/)
├── pkg/            # Libraries (our src/)
├── api/            # API definitions
├── deployments/    # Deployment configs
```

**Netflix/Uber Microservices**:
```
├── apps/           # Independent applications
├── libs/           # Shared libraries  
├── tools/          # Development tools
├── infra/          # Infrastructure
```

### Technical Benefits

1. **Clean Import Paths**:
   ```python
   # Clean and logical
   from apps.llm_server import api
   from services.model_watcher import watcher
   from src.common import utils
   
   # vs nested complexity
   from src.apps.backend.services.llm_server.api.v1 import endpoints
   ```

2. **Independent Deployment**:
   - Each app can have its own Dockerfile
   - Services can scale independently  
   - Tools don't deploy to production

3. **Team Ownership**:
   ```
   apps/llm-server/     → Backend API Team
   apps/dashboard/      → Frontend Team
   services/vector-db/  → Infrastructure Team  
   tools/cli/          → Developer Experience Team
   ```

4. **CI/CD Pipeline Natural Fit**:
   ```yaml
   build-apps:
     matrix: [llm-server, memory-server, dashboard]
   
   build-services:
     matrix: [model-watcher, vector-db, auth-service] 
   
   build-tools:
     matrix: [cli, vscode-extension, web-scraper]
   ```

### Future-Proofing

This structure accommodates predictable growth:

**Apps (User-facing applications)**:
- ✅ `llm-server/` (existing)
- ✅ `memory-server/` (existing)
- 🔄 `dashboard/` (planned)
- 🔄 `api-gateway/` (when scaling)
- 🔄 `admin-panel/` (management)
- 🔄 `mobile-api/` (if mobile app needed)

**Services (Background/support services)**:
- ✅ `model-watcher/` (existing)
- 🔄 `vector-db/` (planned)
- 🔄 `auth-service/` (when scaling)
- 🔄 `model-registry/` (model management)
- 🔄 `telemetry/` (monitoring)

**Tools (Developer experience)**:
- ✅ `cli/` (open-interpreter, opencode)
- ✅ `vscode-extension/` (existing)
- ✅ `web-scraper/` (existing)
- ✅ `mcp-servers/` (existing)

## Consequences

### Positive
- ✅ Clear conceptual separation of concerns
- ✅ Supports independent development teams
- ✅ Enables microservices architecture migration
- ✅ Industry-standard patterns for easier onboarding
- ✅ Clean CI/CD pipeline organization
- ✅ Scalable for future growth

### Negative
- ⚠️ Requires updating existing import paths and scripts
- ⚠️ Some initially deeper navigation (but logically organized)
- ⚠️ Need to educate team on new structure

### Neutral
- 🔄 Migration effort required (one-time cost)
- 🔄 Need to update documentation and READMEs

## Implementation Notes

1. **Migration Strategy**: Move directories in phases to minimize disruption
2. **Script Updates**: Update all relative paths in startup scripts
3. **Import Updates**: Update Python imports throughout codebase
4. **Documentation**: Update all README files with new structure
5. **CI/CD Updates**: Modify build pipelines to match new structure

## References

- [Microsoft .NET Project Structure Guidelines](https://docs.microsoft.com/en-us/dotnet/core/porting/project-structure)
- [Google Go Project Layout](https://github.com/golang-standards/project-layout)
- [Netflix Microservices Architecture](https://netflixtechblog.com/tagged/microservices)
- [Monorepo Tools and Best Practices](https://monorepo.tools/)

---

**Next ADRs to consider**:
- ADR-002: Inter-Service Communication Patterns  
- ADR-003: Configuration Management Strategy
- ADR-004: Logging and Monitoring Architecture