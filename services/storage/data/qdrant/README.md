# Qdrant Vector Database Storage

## Directory Structure

This directory contains Qdrant's persistent storage for vector databases and metadata.

### Files
- `.lock` - Database lock file to prevent concurrent access
- `meta.json` - Database metadata and configuration
- `qdrant_config.yaml` - Performance and optimization settings
- `collections/` - Collection-specific data storage

### Persistence Configuration

Qdrant is configured for embedded mode with the following persistence settings:

- **Storage Location**: `/services/storage/data/qdrant/`
- **Memory Mapping**: Enabled for zero-copy reads
- **Snapshots**: Automatic backup and recovery support  
- **Write-Ahead Logging**: Durability guarantees for all operations
- **Collection Metadata**: Persistent across restarts

### Backup Strategy

1. **Snapshots**: Automatic snapshots for data protection
2. **WAL**: Write-ahead logging prevents data loss
3. **Metadata**: Schema and configuration backup included
4. **Recovery**: Automatic recovery on restart

### Storage Management

- Collections are stored in separate subdirectories
- Memory-mapped files enable efficient access
- Automatic cleanup of deleted data
- Index optimization runs periodically

### Performance Notes

- Storage is optimized for ARM64 architecture
- Memory usage limited to 25% of available RAM (32GB)
- Scalar quantization reduces storage by 4x
- HNSW indices balance accuracy and speed

## Usage

The persistence directory is automatically managed by Qdrant. No manual intervention required for normal operations.