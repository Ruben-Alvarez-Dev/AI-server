# Config Directory Overview

This directory contains YAML configuration templates used across the system:

- `system.yaml`: Global system settings (ports, timeouts, paths, resource limits)
- `profiles.yaml`: LLM profiles (DEV, PRODUCTIVITY, ACADEMIC, GENERAL)
- `models.yaml`: Model definitions (quantization, context, GPU layers, checksums)
- `autocleanup.yaml`: Cleanup policies (TTL, IPC thresholds, schedules)
- `messaging.yaml`: Messaging layer (Pulsar, NATS, Benthos)
- `monitoring.yaml`: Observability (Prometheus scrape, alerts)
- `gui.yaml`: GUI Server (dashboards, refresh, sockets)
- `endpoints.yaml`: Dynamic API routes configuration

Notes:
- Values are documented in English; never commit secrets. Use `.env` for sensitive values.
- Use environment variables to override defaults where supported.
- ATLAS remains a black box; configure only its public endpoints and timeouts.
