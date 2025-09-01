# Chapter 4: Storage Infrastructure
**39 tasks | Phase 2 | Prerequisites: Chapter 3 completed**

## 4.1 DuckDB Setup (7 tasks)

- [x] **4.1.1 Install DuckDB 0.10.x Python package**  
  Install DuckDB using pip install duckdb==0.10.0 for embedded analytical database capabilities. DuckDB provides excellent OLAP performance with minimal resource usage. It's perfect for time-series data and analytical queries.

- [x] **4.1.2 Install DuckDB CLI tools**  
  Download and install DuckDB CLI for interactive querying and database management tasks. The CLI is useful for debugging and manual operations. Add to PATH for system-wide availability.

- [x] **4.1.3 Create data directory structure**  
  Create /services/storage/data/duckdb/ with subdirectories for different data categories (hierarchy, metrics, logs). Organize by date partitions for efficient querying and cleanup. Include README explaining the structure.

- [x] **4.1.4 Configure memory limits (20% available)**  
  Set DuckDB memory limit to 20% of detected available RAM using SET memory_limit='25GB' in initialization. This prevents DuckDB from consuming memory needed for models. Configure spill-to-disk behavior for large queries.

- [x] **4.1.5 Setup partitioning templates**  
  Create partitioning schemes for time-series data using DuckDB's native partitioning by day/week/month. This enables efficient data pruning and query performance. Document partitioning strategy and maintenance procedures.

- [x] **4.1.6 Create initial schemas**  
  Define schemas for hierarchy levels, metrics, and system events with appropriate data types and constraints. Include indexes for common query patterns. Version schemas for migration support.

- [x] **4.1.7 Test connection and queries**  
  Verify Python connection to DuckDB and run test queries to ensure proper setup. Benchmark query performance for expected workloads. Document connection pooling and concurrent access patterns.

## 4.2 Qdrant Vector Database (8 tasks)

- [x] **4.2.1 Download Qdrant embedded binary**  
  Download Qdrant binary for macOS ARM64 from GitHub releases for embedded vector search capabilities. Choose the embedded version to avoid running separate server process. Verify checksum for integrity.

- [x] **4.2.2 Configure embedded mode**  
  Configure Qdrant to run embedded within Python process, eliminating network overhead and simplifying deployment. Set up in-process communication for maximum performance. This mode is ideal for single-node deployments.

- [x] **4.2.3 Set memory limits (25% available)**  
  Configure Qdrant to use maximum 25% of available RAM for vector indexes, with the rest memory-mapped from disk. This balances search performance with memory availability for other components. Include cache size configuration.

- [x] **4.2.4 Configure HNSW parameters**  
  Tune HNSW index parameters: M=16 for connectivity, ef_construct=100 for index quality, ef=50 for search quality. These settings balance accuracy with performance for our embedding dimensions. Document trade-offs for tuning.

- [x] **4.2.5 Enable scalar quantization**  
  Enable scalar quantization to reduce memory usage by 4x with minimal accuracy loss. This allows storing more vectors in RAM for faster searches. Configure quantization parameters based on embedding characteristics.

- [x] **4.2.6 Setup persistence directory**  
  Create /services/storage/data/qdrant/ for persistent storage of vectors and metadata. Configure snapshots and write-ahead logging for durability. Include backup procedures in documentation.

- [x] **4.2.7 Create initial collections**  
  Set up collections for different embedding types: code, documents, summaries with appropriate vector dimensions. Configure metadata fields for filtering. Include collection versioning strategy.

- [x] **4.2.8 Test vector operations**  
  Insert test vectors and verify search, update, and delete operations work correctly. Benchmark search performance with realistic data volumes. Document performance characteristics and scaling limits.

## 4.3 Neo4j Embedded Setup (8 tasks)

- [ ] **4.3.1 Install Neo4j embedded JAR**  
  Download Neo4j embedded JAR files and configure Python JVM bridge for graph database functionality. The embedded mode avoids running separate Neo4j server. Configure JVM parameters for ARM64 optimization.

- [ ] **4.3.2 Install py2neo Python driver**  
  Install py2neo using pip install py2neo for Pythonic interface to Neo4j operations. This driver provides high-level abstractions for graph operations. Configure connection pooling and transaction management.

- [ ] **4.3.3 Configure heap limits (15% available)**  
  Set Neo4j JVM heap to 15% of available RAM using -Xmx19GB -Xms19GB for predictable performance. Fixed heap size prevents garbage collection pauses. Configure G1GC for low-latency operation.

- [ ] **4.3.4 Setup page cache (10% additional)**  
  Configure Neo4j page cache to 10% of RAM (13GB) for caching graph data from disk. This cache dramatically improves traversal performance. Monitor cache hit rates for tuning.

- [ ] **4.3.5 Create data directory**  
  Initialize /services/storage/data/neo4j/ for graph storage with proper permissions and structure. Configure transaction logs and checkpoint behavior. Include growth management strategy.

- [ ] **4.3.6 Initialize graph database**  
  Create initial graph database with configured storage engine and settings. Import any seed data or schema constraints. Configure indexes for common query patterns.

- [ ] **4.3.7 Create indexes**  
  Define indexes on frequently queried properties: entity names, types, timestamps, and relationship types. These indexes enable efficient graph queries. Include full-text indexes for search operations.

- [ ] **4.3.8 Test Cypher queries**  
  Run test Cypher queries to verify graph operations: node creation, relationship creation, and traversals. Benchmark performance for expected query patterns. Document query optimization techniques.

## 4.4 SQLite Configuration (6 tasks)

- [ ] **4.4.1 Verify SQLite3 installed**  
  Check SQLite3 is available (comes with Python) and verify version is 3.35+ for modern features. SQLite provides lightweight persistent storage for configuration and metadata. Document version requirements.

- [ ] **4.4.2 Configure WAL mode**  
  Enable Write-Ahead Logging mode using PRAGMA journal_mode=WAL for better concurrency and performance. WAL allows readers and writers to work simultaneously. Configure checkpoint behavior.

- [ ] **4.4.3 Set cache size to 500MB**  
  Configure SQLite page cache to 500MB using PRAGMA cache_size=-500000 for improved query performance. This cache reduces disk I/O for frequently accessed data. Monitor memory usage and adjust as needed.

- [ ] **4.4.4 Create database files**  
  Initialize SQLite databases for configuration, axioms, and permanent storage in /services/storage/data/sqlite/. Use separate files for different data categories. Configure auto-vacuum and integrity checks.

- [ ] **4.4.5 Setup schemas**  
  Create schemas for storing hierarchical axioms, configuration history, and system metadata. Include appropriate indexes and constraints. Version schemas for migration support.

- [ ] **4.4.6 Configure auto-vacuum**  
  Enable incremental auto-vacuum using PRAGMA auto_vacuum=INCREMENTAL to reclaim space from deleted data. This prevents database bloat over time. Schedule periodic vacuum operations.

## 4.5 LanceDB Installation (5 tasks)

- [ ] **4.5.1 Install LanceDB via pip**  
  Install LanceDB using pip install lancedb for columnar storage optimized for ML workloads. LanceDB provides versioned storage perfect for embeddings evolution. It's built in Rust for performance.

- [ ] **4.5.2 Create data directories**  
  Set up /services/storage/data/lancedb/ with subdirectories for different embedding types and versions. Organize for efficient access patterns. Include cleanup policies for old versions.

- [ ] **4.5.3 Configure memory mapping**  
  Enable memory-mapped file access for zero-copy reads and optimal performance. Configure mmap settings based on available RAM and file sizes. This approach minimizes memory overhead.

- [ ] **4.5.4 Setup version control**  
  Configure LanceDB's built-in version control for tracking embedding changes over time. Set retention policies for old versions. This enables rollback and experimentation.

- [ ] **4.5.5 Test basic operations**  
  Verify LanceDB can create tables, insert vectors, and perform searches. Test version control operations. Benchmark performance compared to Qdrant for different use cases.

## 4.6 Cache Layer (6 tasks)

- [ ] **4.6.1 Install DragonflyDB via Homebrew**  
  Install DragonflyDB using brew install dragonflydb as a modern Redis-compatible cache optimized for modern hardware. DragonflyDB provides better performance than Redis on multi-core systems. It's perfect for our caching needs.

- [ ] **4.6.2 Configure memory limit (2GB)**  
  Set DragonflyDB max memory to 2GB using --maxmemory 2gb to prevent cache from consuming model memory. This limit ensures cache doesn't impact primary operations. Configure memory usage alerts.

- [ ] **4.6.3 Set eviction policy (allkeys-lru)**  
  Configure LRU eviction policy using --maxmemory-policy allkeys-lru to automatically remove least recently used items. This keeps hot data in cache while preventing memory overflow. Monitor eviction rates for sizing.

- [ ] **4.6.4 Disable persistence**  
  Disable persistence features since this is purely a cache layer and data can be regenerated. This improves performance and reduces disk I/O. Document what data is safe to cache.

- [ ] **4.6.5 Start service**  
  Launch DragonflyDB service using launchctl and verify it's listening on Redis port 6379. Check memory usage and performance metrics. Test basic Redis commands for compatibility.

- [ ] **4.6.6 Test Redis compatibility**  
  Verify Redis client libraries can connect and perform basic operations (GET, SET, EXPIRE, etc.). Test data structures like lists and sorted sets. This compatibility enables using existing Redis tools and libraries.

## Progress Summary
- **Total Tasks**: 39
- **Completed**: 15/39
- **Current Section**: 4.3 Neo4j Embedded Setup
- **Next Checkpoint**: 4.3.1
