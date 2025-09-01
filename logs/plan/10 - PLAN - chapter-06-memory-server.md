# Chapter 6: Memory Server MVP
**34 tasks | Phase 4 | Prerequisites: Chapter 5 completed**

## 6.1 Resource Monitor Service (7 tasks)

- [ ] **6.1.1 Implement dynamic resource detector**  
  Create Python service that queries system resources every 30 seconds using psutil and system calls. Calculate available resources after accounting for OS and running applications. This forms the foundation of dynamic resource management.

- [ ] **6.1.2 Create resource allocator**  
  Implement logic to allocate detected resources across services, never exceeding 70% of available capacity. Include safety margins and emergency reserves. This prevents system overload while maximizing utilization.

- [ ] **6.1.3 Setup pressure monitor**  
  Monitor CPU, RAM, disk I/O, and GPU utilization to calculate system pressure metrics. Combine into unified pressure score for decision making. This enables proactive resource management.

- [ ] **6.1.4 Implement mode controller**  
  Create state machine that switches between Normal, Moderate, High, Critical, and Emergency modes based on pressure. Each mode has different operational characteristics. This provides graceful degradation under load.

- [ ] **6.1.5 Create monitoring loop (30s interval)**  
  Implement async loop that runs detection, calculation, and adjustment every 30 seconds. Use asyncio for non-blocking operation. This frequency balances responsiveness with overhead.

- [ ] **6.1.6 Setup IPC calculator**  
  Implement Composite Pressure Index calculation weighing Disk (40%), RAM (30%), CPU (20%), I/O (10%). This unified metric drives cleanup and operational decisions. The weights reflect relative importance.

- [ ] **6.1.7 Test resource detection accuracy**  
  Verify resource detection matches actual system state under various loads. Test with synthetic workloads and real operations. Document detection accuracy and edge cases.

## 6.2 Basic Hierarchy Processor (7 tasks)

- [ ] **6.2.1 Implement L0 raw data ingestion**  
  Create ingestion endpoint that accepts raw events and stores them with Zstandard compression. Implement async processing to avoid blocking. This layer preserves all original data.

- [ ] **6.2.2 Create L1 chunking system**  
  Implement semantic chunking that breaks documents into 512-2048 token segments with overlap. Use sentence boundaries for clean breaks. This prepares data for embedding and retrieval.

- [ ] **6.2.3 Implement L2 summarization**  
  Create summarization pipeline using Phi-3-Mini-128K for hierarchical document compression. Maintain key information while reducing size 50:1. This layer provides quick overviews.

- [ ] **6.2.4 Setup TTL management**  
  Implement time-to-live tracking with dynamic adjustment based on IPC score. Create cleanup tasks for expired data. This ensures automatic space management.

- [ ] **6.2.5 Configure compression (Zstandard)**  
  Setup Zstandard compression with level 3 for L0, level 9 for L2, using shared dictionaries. This reduces storage requirements significantly. Balance compression ratio with CPU usage.

- [ ] **6.2.6 Create storage interfaces**  
  Build abstraction layer for storage operations across DuckDB, files, and future backends. Use repository pattern for clean architecture. This enables storage backend flexibility.

- [ ] **6.2.7 Test data flow L0→L1→L2**  
  Verify data correctly flows through hierarchy levels with proper transformation and storage. Test with various document types. Document processing times and compression achieved.

## 6.3 Memory Server API (8 tasks)

- [ ] **6.3.1 Create Flask application structure**  
  Initialize Flask app with blueprints for ingestion, search, and management endpoints. Use application factory pattern for testing. This provides clean API organization.

- [ ] **6.3.2 Implement /api/v1/ingest endpoint**  
  Create POST endpoint that accepts documents/events and queues them for processing. Return immediately with job ID for async processing. This enables high ingestion throughput.

- [ ] **6.3.3 Implement /api/v1/search/simple endpoint**  
  Build basic vector search endpoint using Qdrant for similarity search. Return ranked results with metadata. This provides core retrieval functionality.

- [ ] **6.3.4 Implement /api/v1/status endpoint**  
  Create health check endpoint returning system status, IPC score, and resource usage. Include component health checks. This enables monitoring and alerting.

- [ ] **6.3.5 Add error handling middleware**  
  Implement global error handler that returns consistent JSON error responses with appropriate HTTP codes. Include request ID for tracing. This improves API usability and debugging.

- [ ] **6.3.6 Setup structured logging**  
  Configure loguru to output structured JSON logs with request context and tracing information. Include performance metrics in logs. This enables log analysis and debugging.

- [ ] **6.3.7 Configure CORS policies**  
  Setup CORS to allow GUI Server and authorized origins while blocking unauthorized access. Include preflight handling. This enables secure browser-based access.

- [ ] **6.3.8 Test API endpoints**  
  Write integration tests for all endpoints verifying correct behavior and error handling. Test with realistic payloads. Document API with examples.

## 6.4 Basic Cleanup Daemon (7 tasks)

- [ ] **6.4.1 Create cleanup orchestrator**  
  Build central coordinator that manages all cleanup operations based on schedules and triggers. Use priority queue for cleanup tasks. This ensures organized space management.

- [ ] **6.4.2 Implement IPC-based TTL adjustment**  
  Create dynamic TTL adjustment that reduces retention as IPC increases. Use exponential decay for aggressive cleanup. This provides automatic space management under pressure.

- [ ] **6.4.3 Setup continuous monitoring**  
  Implement background task that continuously monitors space usage and triggers cleanup as needed. Use event-driven architecture. This prevents space exhaustion.

- [ ] **6.4.4 Create 5-minute cleanup tasks**  
  Implement quick cleanup tasks: temp file removal, cache trimming, log rotation. Keep operations under 10 seconds. These maintain system hygiene.

- [ ] **6.4.5 Create hourly cleanup tasks**  
  Build deeper cleanup: database vacuum, index optimization, compression of old data. Allow up to 5 minutes runtime. These tasks maintain performance.

- [ ] **6.4.6 Create daily cleanup schedule**  
  Implement comprehensive cleanup at 3 AM: full vacuum, reindexing, pattern extraction, report generation. Can take up to 30 minutes. This ensures long-term health.

- [ ] **6.4.7 Test cleanup under pressure**  
  Simulate high IPC scenarios and verify cleanup responds appropriately. Test emergency cleanup triggers. Document cleanup effectiveness.

## 6.5 Memory Server Scripts (5 tasks)

- [ ] **6.5.1 Create start.sh script**  
  Write bash script that starts Memory Server with proper environment, waits for ready state, and reports status. Include dependency checks. This simplifies operations.

- [ ] **6.5.2 Create stop.sh script**  
  Implement graceful shutdown script that stops ingestion, completes processing, and cleanly shuts down. Include timeout handling. This prevents data loss.

- [ ] **6.5.3 Create cleanup.py utility**  
  Build manual cleanup utility with options for aggressive cleanup, specific levels, or date ranges. Include dry-run mode. This provides operational flexibility.

- [ ] **6.5.4 Setup log rotation**  
  Configure logrotate or Python logging to rotate logs daily, compress old logs, and maintain 30 days history. Prevent disk filling from logs. This ensures log management.

- [ ] **6.5.5 Create health check script**  
  Write monitoring script that verifies all Memory Server components are healthy and responding. Return appropriate exit codes. This enables automated monitoring.

## Progress Summary
- **Total Tasks**: 34
- **Completed**: 0/34
- **Current Section**: 6.1 Resource Monitor
- **Next Checkpoint**: 6.1.1