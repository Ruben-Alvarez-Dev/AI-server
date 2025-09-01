# Neo4j Data Directory Structure

This directory contains Neo4j database files, transaction logs, and system logs for the AI server graph database.

## Directory Structure

```
/services/storage/neo4j/data/
├── databases/          # Graph database files
├── transactions/       # Transaction logs and checkpoint files  
├── logs/              # System and query logs
└── README.md          # This documentation
```

## Directory Purposes

### `/databases/`
- **Purpose**: Contains Neo4j graph database files
- **Contents**: Node stores, relationship stores, property stores, indexes
- **Size**: Grows with graph data - expect GBs for large graphs
- **Backup**: Critical for data recovery - include in backups

### `/transactions/`  
- **Purpose**: Write-ahead transaction logs for ACID compliance
- **Contents**: Transaction entries, checkpoint metadata
- **Size**: Moderate - logs are rotated and archived
- **Backup**: Important for consistency - include in backups

### `/logs/`
- **Purpose**: Neo4j system logs, query logs, debug information
- **Contents**: neo4j.log, query.log, debug.log, gc.log
- **Size**: Configurable rotation - typically MBs per day
- **Backup**: Optional - useful for debugging and monitoring

## Configuration

This data directory is configured in Neo4j settings:

```properties
# In neo4j.conf
server.directories.data=/path/to/this/directory
server.directories.logs=/path/to/this/directory/logs  
server.directories.transaction.logs.root=/path/to/this/directory/transactions
```

## Permissions

Ensure Neo4j process has read/write access to all subdirectories:

```bash
chmod -R 755 /services/storage/neo4j/data/
chown -R neo4j:neo4j /services/storage/neo4j/data/  # If running with neo4j user
```

## Monitoring

Monitor disk usage and growth:

```bash
# Check directory sizes
du -sh /services/storage/neo4j/data/*

# Monitor active files
lsof +D /services/storage/neo4j/data/
```

## Backup Strategy

Include in backup procedures:
1. **databases/**: Full backup required
2. **transactions/**: Include for consistency
3. **logs/**: Optional - for debugging only

## Performance Notes

- **SSD recommended**: Graph databases benefit from fast random I/O
- **Page cache**: 12GB configured to cache hot data in memory
- **File system**: Ensure adequate space - graph data can grow quickly
- **I/O monitoring**: Watch for disk bottlenecks during heavy operations

## Troubleshooting

Common issues:
- **Disk full**: Monitor space usage and set up alerts
- **Permission errors**: Verify read/write access for Neo4j process  
- **Corruption**: Use Neo4j consistency checker if database issues occur
- **Performance**: Monitor I/O wait times and page cache hit rates

For more information, see Neo4j operations documentation.