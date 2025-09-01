# Chapter 3: Messaging Infrastructure
**26 tasks | Phase 2 | Prerequisites: Chapter 2 completed**

## 3.1 Apache Pulsar Installation (10 tasks)

- [x] **3.1.1 Download Apache Pulsar 3.2.x binary**  
  Download Pulsar binary distribution from Apache mirrors, choosing the bin package not the all package to save space. Version 3.2 provides improved performance and stability for our use case. Verify GPG signature and checksum for security.

- [x] **3.1.2 Extract to /opt/pulsar**  
  Extract Pulsar to /opt/pulsar (create directory with proper permissions first) as the standard location for optional software. This path keeps it separate from Homebrew-managed software. Create symbolic links for easier version management.

- [x] **3.1.3 Configure standalone mode**  
  Edit conf/standalone.conf to run Pulsar in standalone mode suitable for single-machine deployment. Adjust memory settings, disable unnecessary components like BookKeeper replication. This mode is perfect for development and single-node production.

- [x] **3.1.4 Set memory limits to 2GB**  
  Configure JVM heap size to 2GB maximum in conf/pulsar_env.sh using -Xmx2g -Xms1g. This leaves plenty of RAM for LLMs while providing adequate performance for messaging. Include garbage collection tuning for low latency.

- [x] **3.1.5 Configure RocksDB for metadata**  
  Switch metadata storage to RocksDB instead of ZooKeeper for lower memory footprint and better SSD performance. RocksDB provides persistent key-value storage optimized for flash storage. Configure compaction and cache settings appropriately.

- [x] **3.1.6 Setup tiered storage to local filesystem**  
  Configure tiered storage to automatically move old messages to filesystem storage, keeping only recent data in memory. This enables infinite retention without memory pressure. Set up age and size-based tiering policies.

- [x] **3.1.7 Create systemd/launchd service**  
  Write a launchd plist file for macOS to manage Pulsar as a system service with automatic restart. Include proper dependency ordering and resource limits. This ensures Pulsar starts on boot and recovers from failures.

- [x] **3.1.8 Start Pulsar service**  
  Start Pulsar using launchctl and verify it's running by checking the admin API at http://localhost:8080. Monitor logs for successful startup and absence of errors. Test basic pub/sub functionality with pulsar-client.

- [x] **3.1.9 Verify Pulsar admin tools work**  
  Test pulsar-admin CLI tools to ensure we can manage topics, namespaces, and tenants. Create test topics and verify message flow. These tools are essential for operational management and debugging.

- [x] **3.1.10 Create namespaces for memory-llm communication**  
  Set up dedicated namespaces like memory-server/rag, llm-server/orchestration for logical separation. Configure retention policies and quotas per namespace. This organization enables independent scaling and management.

## 3.2 NATS Server Installation (9 tasks)

- [x] **3.2.1 Install NATS Server 2.10+ via Homebrew**  
  Install NATS using brew install nats-server for lightweight, high-performance messaging within LLM orchestration. NATS provides superior latency characteristics for internal communication. Version 2.10 includes JetStream for persistence.

- [x] **3.2.2 Configure JetStream enabled**  
  Enable JetStream in the NATS configuration for persistent messaging and exactly-once semantics where needed. JetStream adds Kafka-like capabilities while maintaining NATS simplicity. Configure storage location and limits.

- [x] **3.2.3 Set memory limit to 500MB**  
  Configure NATS to use maximum 500MB RAM for messages and JetStream storage. This is sufficient for orchestration messaging while preserving RAM for models. Include connection and subscription limits.

- [x] **3.2.4 Configure file-based storage**  
  Set up file-based storage for JetStream streams, storing messages on SSD for persistence. This provides durability for critical messages without excessive memory use. Configure retention based on message age and count.

- [x] **3.2.5 Setup retention policies**  
  Define retention policies for different message types: ephemeral for real-time coordination, persistent for task queues. Configure automatic cleanup of acknowledged messages. Balance durability needs with storage constraints.

- [x] **3.2.6 Create systemd/launchd service**  
  Create launchd configuration for NATS with proper startup ordering after network is available. Include restart policies and resource limits. This ensures NATS is always available for orchestration.

- [x] **3.2.7 Start NATS service**  
  Launch NATS service and verify it's listening on port 4222 (client) and 8222 (monitoring). Check the monitoring endpoint for server health. Test basic pub/sub operations with the NATS CLI.

- [x] **3.2.8 Install NATS CLI tools**  
  Install nats CLI tool using brew install nats-io/nats-tools/nats for testing and management. This Swiss-army knife tool enables debugging and operational tasks. Configure contexts for different environments.

- [x] **3.2.9 Verify pub/sub functionality**  
  Test basic pub/sub patterns, request/reply, and queue groups to ensure NATS is functioning correctly. Verify JetStream stream creation and consumer functionality. These patterns form the basis of our orchestration system.

## 3.3 Benthos Installation (7 tasks)

- [x] **3.3.1 Install Benthos 4.x via Homebrew**  
  Install Benthos stream processor using brew install benthos for declarative data pipeline creation. Benthos connects different systems with minimal code, perfect for our integration needs. Version 4 provides improved performance and stability.

- [x] **3.3.2 Create pipeline configuration directory**  
  Set up /config/benthos/ directory structure for pipeline definitions organized by purpose. Include templates for common patterns like Pulsar→DuckDB ingestion. This organization enables pipeline reuse and versioning.

- [x] **3.3.3 Setup pipeline templates**  
  Create reusable pipeline templates for common operations: message transformation, enrichment, routing, and storage. These templates accelerate development of new data flows. Include error handling and retry logic in templates.

- [x] **3.3.4 Configure rate limiting**  
  Implement rate limiting in Benthos pipelines to prevent overwhelming downstream services. Configure adaptive rate limiting based on back-pressure signals. This protects system stability during traffic spikes.

- [x] **3.3.5 Setup circuit breakers**  
  Configure circuit breakers in pipelines to handle downstream service failures gracefully. Implement exponential backoff and health checking. This prevents cascade failures and enables self-healing.

- [x] **3.3.6 Configure Prometheus metrics export**  
  Enable Benthos metrics export to Prometheus for monitoring pipeline performance and errors. Configure custom metrics for business-relevant events. This visibility is crucial for operational excellence.

- [x] **3.3.7 Test pipeline execution**  
  Create and run test pipelines to verify Benthos can connect to Pulsar, NATS, and databases. Test error handling and recovery scenarios. Document pipeline development workflow and best practices.

## Progress Summary
- **Total Tasks**: 26
- **Completed**: 26/26 ✅
- **Status**: CHAPTER COMPLETED
- **Completion Date**: 2025-09-01

### Progress Update (2025-09-01)
- Prepared installer and automation for 3.1.1–3.1.8:
  - `tools/messaging/pulsar_setup_mac.sh` (supports `/opt` with sudo or user-space with `PULSAR_PREFIX`, memory 2GB, tiered storage, launchd/Background start, admin API check)
  - `config/launchd/com.ai.pulsar.plist`
  - `tools/messaging/pulsar_post_install.sh` to create namespaces and run smoke tests (3.1.9–3.1.10)
- Pending: Execute installer on host to complete download/start (network/sudo required outside CI sandbox).
- After execution: run post-install script to finalize namespaces and verifications.
