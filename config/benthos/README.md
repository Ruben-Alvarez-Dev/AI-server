# Benthos Pipeline Configuration

## Directory Structure

- `templates/` - Reusable pipeline templates
- `pipelines/` - Active pipeline configurations
- `schemas/` - Message schema definitions

## Common Patterns

### Pulsar → DuckDB Ingestion
Transform and store messages from Pulsar topics into DuckDB for analytics.

### NATS → Pulsar Bridge
Route orchestration messages between NATS and Pulsar systems.

### Data Enrichment
Enrich messages with metadata and context information.

## Configuration Guidelines

1. Use environment variables for connection strings
2. Include error handling and retry logic
3. Configure rate limiting and backpressure
4. Export metrics to Prometheus
5. Use circuit breakers for downstream services