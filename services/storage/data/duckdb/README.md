# DuckDB Data Directory Structure

## Directory Organization

### `/hierarchy/`
Storage for memory hierarchy data and relationships.

### `/metrics/`
System performance metrics and analytical data.

### `/logs/`
Application and system log data for analysis.

### `/partitions/`
Date-partitioned data organized for efficient querying and cleanup.

## Data Management

### Partitioning Strategy
- **Daily**: `/partitions/YYYY/MM/DD/` for high-frequency data
- **Weekly**: `/partitions/YYYY/WW/` for aggregated data
- **Monthly**: `/partitions/YYYY/MM/` for historical data

### Cleanup Policies
- Daily partitions: Keep last 30 days
- Weekly partitions: Keep last 12 weeks
- Monthly partitions: Keep last 24 months

### File Naming Convention
- `{category}_{date}_{sequence}.db` - Main data files
- `{category}_{date}_idx.db` - Index files
- `{category}_{date}_meta.json` - Metadata files

## Usage Notes

1. Each category should use separate database files for optimal performance
2. Use date partitioning for efficient data pruning
3. Include metadata files for schema versioning
4. Monitor disk usage and implement cleanup procedures