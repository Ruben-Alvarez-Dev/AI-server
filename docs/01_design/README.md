# Design Documentation

**System architecture, decisions, and research foundations**

*Read these documents to understand what the AI-Server is and how it's designed.*

---

## 📋 Reading Order

1. **[Architecture Decisions Overview](01_overview-architecture-decisions.md)**
   - Why we chose this directory structure
   - Key architectural decisions and rationale
   - Industry comparisons and justifications

2. **[Project Structure Guide](02_project-structure-guide.md)**
   - Complete directory organization
   - Purpose of each component
   - Scalability and team ownership patterns

3. **[System Architecture](03_system-architecture.md)**
   - Overall system design
   - Component interactions
   - Technology stack decisions

4. **[Memory Server Design](04_memory-server-design.md)**
   - LazyGraphRAG implementation
   - Advanced retrieval patterns
   - Performance optimizations

5. **[Memory Server Research](05_memory-server-research.md)**
   - Research background
   - Comparative analysis
   - Design trade-offs

---

## 🎯 Key Concepts

### Multi-App Architecture
Enterprise-grade separation of concerns:
- **apps/**: User-facing applications
- **services/**: Background support services  
- **tools/**: Development utilities

### Design Principles
- Team scalability and ownership
- Independent deployment capability
- Industry-standard patterns
- Future-proof extensibility

### Technology Decisions
- FastAPI for high-performance APIs
- LazyGraphRAG for intelligent memory
- Docker/Kubernetes for deployment
- OpenAI-compatible interfaces

---

**Next**: Once you understand the design, proceed to [Installation](../02_installation/)