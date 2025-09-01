# DuckDB Data Directory Structure

This directory contains the organized data structure for DuckDB analytical databases in the AI server storage layer.

## Directory Structure

```
/services/storage/data/duckdb/
├── hierarchy/          # Knowledge graph and entity relationship data
│   ├── entities/       # Entity nodes (users, documents, concepts)
│   ├── relationships/  # Relationship edges and connections
│   └── semantic/       # Semantic mappings and ontologies
├── metrics/            # Time-series metrics and analytical data
│   ├── performance/    # System performance metrics
│   ├── usage/          # User interaction and usage statistics
│   └── business/       # Business intelligence and KPI data
└── logs/               # Log aggregation and analysis data
    ├── access/         # Access logs and audit trails
    ├── error/          # Error logs and debugging data
    └── system/         # System events and operational logs
```

## Partitioning Strategy

### Time-based Partitioning
- **Metrics data**: Partitioned by day/month for optimal query performance
- **Log data**: Daily partitions with automatic cleanup policies
- **Historical data**: Archived to separate databases for long-term storage

### Entity-based Partitioning
- **Large entities**: Split across multiple files by entity type
- **Relationships**: Partitioned by relationship strength/frequency
- **Semantic data**: Organized by domain and context

## Database Files

### Naming Convention
```
{category}_{partition}_{date}.duckdb
```

Examples:
- `metrics_performance_2025-01.duckdb`
- `hierarchy_entities_users.duckdb`
- `logs_access_2025-01-09.duckdb`

### File Size Management
- **Target size**: 1-10GB per database file for optimal performance
- **Automatic splitting**: When files exceed 10GB
- **Compression**: Automatic column-store compression

## Usage Examples

### Creating Partitioned Tables
```sql
-- Create time-partitioned metrics table
CREATE TABLE metrics_performance (
    timestamp TIMESTAMP,
    metric_name VARCHAR,
    value DOUBLE,
    tags MAP(VARCHAR, VARCHAR)
) PARTITION BY (DATE_TRUNC('day', timestamp));

-- Create entity hierarchy table
CREATE TABLE hierarchy_entities (
    entity_id UUID PRIMARY KEY,
    entity_type VARCHAR,
    properties MAP(VARCHAR, VARCHAR),
    created_at TIMESTAMP
);
```

### Query Examples
```sql
-- Query recent performance metrics
SELECT metric_name, AVG(value) as avg_value
FROM metrics_performance
WHERE timestamp >= NOW() - INTERVAL 24 HOUR
GROUP BY metric_name;

-- Analyze entity relationships
SELECT e1.entity_type, e2.entity_type, COUNT(*) as connections
FROM hierarchy_entities e1
JOIN hierarchy_relationships r ON e1.entity_id = r.source_id
JOIN hierarchy_entities e2 ON r.target_id = e2.entity_id
GROUP BY e1.entity_type, e2.entity_type;
```

## Maintenance

### Backup Strategy
- Daily incremental backups of active partitions
- Weekly full backups of complete datasets
- Monthly archival to cold storage

### Cleanup Policies
- **Metrics**: Retain 90 days of detailed data, 1 year aggregated
- **Logs**: Retain 30 days of detailed logs, 6 months aggregated
- **Hierarchy**: No automatic cleanup, manual archival

### Performance Optimization
- Regular ANALYZE to update statistics
- Periodic VACUUM to reclaim space
- Index maintenance on frequently queried columns

## Integration Points

### With Python Services
```python
import duckdb

# Connect to metrics database
conn = duckdb.connect('/path/to/metrics_performance_2025-01.duckdb')

# Execute analytical queries
result = conn.execute("""
    SELECT metric_name, AVG(value) as avg_value
    FROM metrics_performance
    WHERE timestamp >= NOW() - INTERVAL 24 HOUR
    GROUP BY metric_name
""").fetchall()
```

### With CLI Tools
```bash
# Interactive analysis
duckdb /path/to/metrics_performance_2025-01.duckdb

# Batch processing
duckdb /path/to/database.duckdb < analysis_queries.sql
```

## Monitoring

### Health Checks
- Database file integrity checks
- Query performance monitoring
- Storage space utilization tracking

### Alerts
- Database corruption detection
- Query timeout alerts
- Storage capacity warnings (>80% full)

---

**Created**: Task 4.1.3 - DuckDB data directory structure setup
**Purpose**: Organized analytical data storage for AI server operations
**Maintenance**: Review quarterly, update as data patterns evolve