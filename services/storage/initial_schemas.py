#!/usr/bin/env python3
"""
DuckDB Initial Schemas

Creates and manages the initial database schemas for the AI-Server system.
"""

import duckdb
from pathlib import Path
from duckdb_config import get_duckdb_connection
from partitioning_templates import PartitioningTemplates, SCHEMA_TEMPLATES


class SchemaManager:
    """Manages DuckDB schema creation and versioning."""
    
    def __init__(self, data_dir: str = "services/storage/data/duckdb"):
        self.data_dir = Path(data_dir)
        self.templates = PartitioningTemplates()
    
    def create_hierarchy_schemas(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create schemas for memory hierarchy storage."""
        
        # L1 Cache - Hot data (daily partitioned)
        self.templates.create_daily_partition_table(
            conn, "l1_cache", SCHEMA_TEMPLATES["hierarchy_events"]
        )
        
        # L2 Working memory - Recent data (weekly partitioned) 
        self.templates.create_weekly_partition_table(
            conn, "l2_working_memory", SCHEMA_TEMPLATES["hierarchy_events"]
        )
        
        # L3 Long-term memory - Historical data (monthly partitioned)
        self.templates.create_monthly_partition_table(
            conn, "l3_longterm_memory", SCHEMA_TEMPLATES["hierarchy_events"]
        )
        
        # Hierarchy relationships table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hierarchy_relationships (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                parent_id UUID NOT NULL,
                child_id UUID NOT NULL,
                relationship_type VARCHAR(50) NOT NULL,
                strength DOUBLE DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_id, child_id, relationship_type)
            )
        """)
        
        # Create indexes for performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hierarchy_parent 
            ON hierarchy_relationships (parent_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hierarchy_child 
            ON hierarchy_relationships (child_id)
        """)
    
    def create_metrics_schemas(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create schemas for system metrics storage."""
        
        # System metrics (daily partitioned for high frequency data)
        self.templates.create_daily_partition_table(
            conn, "system_metrics", SCHEMA_TEMPLATES["system_metrics"]
        )
        
        # Performance metrics aggregation table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_aggregates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                aggregation_type VARCHAR(20) NOT NULL, -- 'hourly', 'daily', 'weekly'
                time_period TIMESTAMP NOT NULL,
                min_value DOUBLE,
                max_value DOUBLE,
                avg_value DOUBLE,
                sum_value DOUBLE,
                count_value INTEGER,
                percentile_50 DOUBLE,
                percentile_95 DOUBLE,
                percentile_99 DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(metric_name, aggregation_type, time_period)
            )
        """)
        
        # Create index on time_period for efficient queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_perf_time_period 
            ON performance_aggregates (time_period)
        """)
    
    def create_logging_schemas(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create schemas for application logging."""
        
        # Application logs (daily partitioned)
        self.templates.create_daily_partition_table(
            conn, "application_logs", SCHEMA_TEMPLATES["application_logs"]
        )
        
        # Error tracking table for monitoring
        conn.execute("""
            CREATE TABLE IF NOT EXISTS error_tracking (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                error_hash VARCHAR(64) NOT NULL, -- Hash of error message + stack trace
                error_type VARCHAR(100) NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                first_occurrence TIMESTAMP NOT NULL,
                last_occurrence TIMESTAMP NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                severity VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'open', -- 'open', 'resolved', 'ignored'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(error_hash)
            )
        """)
        
        # Index for error tracking queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_status 
            ON error_tracking (status, last_occurrence)
        """)
    
    def create_rag_schemas(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create schemas for RAG (Retrieval Augmented Generation) events."""
        
        # RAG events (daily partitioned for query analysis)
        self.templates.create_daily_partition_table(
            conn, "rag_events", SCHEMA_TEMPLATES["rag_events"]
        )
        
        # Document retrieval cache
        conn.execute("""
            CREATE TABLE IF NOT EXISTS retrieval_cache (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_hash VARCHAR(64) NOT NULL,
                query_embedding DOUBLE[],  -- Store embedding for similarity search
                retrieved_document_ids UUID[],
                confidence_scores DOUBLE[],
                cache_hit_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(query_hash)
            )
        """)
        
        # Index for cache lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_retrieval_query_hash 
            ON retrieval_cache (query_hash)
        """)
    
    def create_system_schemas(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create system-level schemas."""
        
        # Schema versioning table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                schema_name VARCHAR(100) NOT NULL,
                version VARCHAR(20) NOT NULL,
                migration_script TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rollback_script TEXT,
                UNIQUE(schema_name, version)
            )
        """)
        
        # Configuration storage
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_configuration (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                config_key VARCHAR(200) NOT NULL,
                config_value TEXT NOT NULL,
                config_type VARCHAR(20) DEFAULT 'string', -- 'string', 'json', 'number', 'boolean'
                description TEXT,
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(config_key)
            )
        """)
        
        # Index for configuration lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_config_key 
            ON system_configuration (config_key)
        """)
    
    def initialize_all_schemas(self) -> None:
        """Initialize all database schemas."""
        
        print("Initializing DuckDB schemas...")
        
        # Create separate databases for different categories
        databases = {
            "hierarchy": "hierarchy_data",
            "metrics": "metrics_data", 
            "logs": "logs_data",
            "rag": "rag_data",
            "system": "system_data"
        }
        
        for db_type, db_name in databases.items():
            print(f"Creating {db_type} schemas in {db_name}.db...")
            
            conn = get_duckdb_connection(db_name)
            
            try:
                if db_type == "hierarchy":
                    self.create_hierarchy_schemas(conn)
                elif db_type == "metrics":
                    self.create_metrics_schemas(conn)
                elif db_type == "logs":
                    self.create_logging_schemas(conn)
                elif db_type == "rag":
                    self.create_rag_schemas(conn)
                elif db_type == "system":
                    self.create_system_schemas(conn)
                
                # Record schema version (only for system database)
                if db_type == "system":
                    conn.execute("""
                        INSERT INTO schema_versions 
                        (schema_name, version, applied_at) 
                        VALUES (?, '1.0.0', CURRENT_TIMESTAMP)
                        ON CONFLICT (schema_name, version) DO NOTHING
                    """, [db_type])
                
                print(f"✓ {db_type} schemas created successfully")
                
            finally:
                conn.close()
        
        print("All schemas initialized successfully!")
    
    def verify_schemas(self) -> dict:
        """Verify all schemas are created correctly."""
        
        results = {}
        databases = ["hierarchy_data", "metrics_data", "logs_data", "rag_data", "system_data"]
        
        for db_name in databases:
            conn = get_duckdb_connection(db_name)
            
            try:
                # Get table list
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [table[0] for table in tables]
                
                results[db_name] = {
                    "status": "OK",
                    "tables": table_names,
                    "table_count": len(table_names)
                }
                
            except Exception as e:
                results[db_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
            finally:
                conn.close()
        
        return results


if __name__ == "__main__":
    # Initialize schemas
    schema_manager = SchemaManager()
    schema_manager.initialize_all_schemas()
    
    # Verify schemas
    print("\nVerifying schemas...")
    results = schema_manager.verify_schemas()
    
    for db_name, result in results.items():
        print(f"\n{db_name}:")
        if result["status"] == "OK":
            print(f"  ✓ Status: {result['status']}")
            print(f"  ✓ Tables: {result['table_count']}")
            for table in result["tables"]:
                print(f"    - {table}")
        else:
            print(f"  ✗ Status: {result['status']}")
            print(f"  ✗ Error: {result['error']}")