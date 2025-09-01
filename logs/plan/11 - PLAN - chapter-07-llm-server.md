# Chapter 7: LLM Server MVP
**25 tasks | Phase 4 | Prerequisites: Chapter 6 completed**

## 7.1 Model Pool Manager (6 tasks)

- [ ] **7.1.1 Create model loading system**  
  Build model loader that initializes llama.cpp instances with proper configuration per model. Handle GPU memory allocation carefully. This manages the model lifecycle.

- [ ] **7.1.2 Implement memory management**  
  Track memory usage per model and implement safe loading/unloading without OOM errors. Include pre-flight checks. This prevents system crashes.

- [ ] **7.1.3 Setup model caching**  
  Implement model cache that keeps frequently used models loaded and removes idle ones. Use LRU policy with time decay. This optimizes response times.

- [ ] **7.1.4 Create unload mechanism**  
  Build safe model unloading that frees GPU memory completely and handles in-flight requests. Verify memory is released. This enables profile switching.

- [ ] **7.1.5 Implement health checks**  
  Create health monitoring that detects model crashes, hangs, or degraded performance. Include automatic recovery. This ensures reliability.

- [ ] **7.1.6 Setup crash recovery**  
  Implement automatic model restart with exponential backoff on crashes. Preserve request queue during recovery. This provides resilience.

## 7.2 Profile Manager (6 tasks)

- [ ] **7.2.1 Define DEV profile structure**  
  Create YAML structure defining models, parameters, and orchestration flow for development profile. Include all ten models specifications. This provides the configuration schema.

- [ ] **7.2.2 Implement profile loading**  
  Build profile loader that reads configuration and initializes specified models with parameters. Validate configuration completeness. This enables profile activation.

- [ ] **7.2.3 Create profile switching logic**  
  Implement state machine for profile transitions: pause requests, save state, unload models, load new profile. Handle errors gracefully. This enables runtime reconfiguration.

- [ ] **7.2.4 Setup state persistence**  
  Save active profile, model states, and in-flight requests to survive restarts. Use SQLite for persistence. This provides operational continuity.

- [ ] **7.2.5 Implement validation**  
  Validate profile configurations for completeness, resource requirements, and model availability. Reject invalid profiles. This prevents runtime errors.

- [ ] **7.2.6 Test profile transitions**  
  Test switching between profiles under load, verifying no requests are lost and resources are managed. Document switch times. This ensures production readiness.

## 7.3 Basic Orchestra (6 tasks)

- [ ] **7.3.1 Create router component**  
  Build request router that analyzes incoming requests and determines complexity and routing. Use the small router model for speed. This provides intelligent request distribution.

- [ ] **7.3.2 Implement single worker**  
  Start with single worker implementation to establish request processing pipeline. Include timeout and error handling. This provides basic functionality.

- [ ] **7.3.3 Setup NATS communication**  
  Configure NATS subjects for router→worker→response flow with request/reply pattern. Include message schemas. This enables component communication.

- [ ] **7.3.4 Create message protocols**  
  Define JSON message format for requests, responses, and control messages between components. Version the protocol. This ensures interoperability.

- [ ] **7.3.5 Implement error handling**  
  Build comprehensive error handling with retries, fallbacks, and error aggregation. Include circuit breakers. This provides fault tolerance.

- [ ] **7.3.6 Setup timeout management**  
  Implement configurable timeouts at each stage with proper cleanup on timeout. Prevent resource leaks. This ensures responsiveness.

## 7.4 LLM Server API (7 tasks)

- [ ] **7.4.1 Create Flask application**  
  Initialize Flask app with async support for handling concurrent requests efficiently. Use Quart if needed for async. This provides the API foundation.

- [ ] **7.4.2 Implement /v1/execute endpoint**  
  Build main execution endpoint that accepts tasks and returns results through orchestration. Support streaming responses. This is the primary interface.

- [ ] **7.4.3 Implement /v1/profiles endpoint**  
  Create endpoint listing available profiles with their capabilities and resource requirements. Include current active profile. This enables profile discovery.

- [ ] **7.4.4 Implement /v1/status endpoint**  
  Build status endpoint showing orchestration health, model states, and performance metrics. Include queue depths. This enables monitoring.

- [ ] **7.4.5 Add WebSocket support**  
  Implement WebSocket endpoint for streaming responses and real-time updates. Use Socket.IO for compatibility. This enables interactive applications.

- [ ] **7.4.6 Setup streaming responses**  
  Configure Server-Sent Events or chunked transfer for streaming model outputs as generated. Reduce perceived latency. This improves user experience.

- [ ] **7.4.7 Test API functionality**  
  Write comprehensive tests for all endpoints including error cases and edge conditions. Test concurrent requests. This ensures API reliability.

## 7.5 LLM Server Scripts (4 tasks)

- [ ] **7.5.1 Create start.sh script**  
  Write startup script that launches LLM Server with selected profile and waits for ready state. Include pre-flight checks. This simplifies deployment.

- [ ] **7.5.2 Create stop.sh script**  
  Implement graceful shutdown that completes in-flight requests and saves state before stopping. Include force-stop option. This ensures clean shutdowns.

- [ ] **7.5.3 Create switch_profile.py utility**  
  Build command-line tool for switching profiles with progress monitoring and error handling. Include dry-run mode. This enables operational control.

- [ ] **7.5.4 Setup process monitoring**  
  Configure process monitoring using pm2 or supervisor to restart on crashes and collect metrics. Include alerting. This ensures availability.

## Progress Summary
- **Total Tasks**: 25
- **Completed**: 0/25
- **Current Section**: 7.1 Model Pool Manager
- **Next Checkpoint**: 7.1.1