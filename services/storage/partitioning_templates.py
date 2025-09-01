#!/usr/bin/env python3
"""
DuckDB Partitioning Templates

Provides templates and utilities for efficient data partitioning strategies.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import duckdb


class PartitioningTemplates:
    """DuckDB partitioning strategies for different data types."""
    
    @staticmethod
    def create_daily_partition_table(conn: duckdb.DuckDBPyConnection, 
                                   table_name: str, 
                                   schema_sql: str,
                                   partition_column: str = "created_at") -> None:
        """
        Create a daily partitioned table.
        
        Args:
            conn: DuckDB connection
            table_name: Name of the table
            schema_sql: SQL schema definition
            partition_column: Column to partition by (must be DATE/TIMESTAMP)
        """
        # Create the main table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {schema_sql}
            )
        """)
        
        # Create index on partition column for efficient queries
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_{partition_column} 
            ON {table_name} ({partition_column})
        """)
    
    @staticmethod
    def create_weekly_partition_table(conn: duckdb.DuckDBPyConnection,
                                    table_name: str,
                                    schema_sql: str,
                                    partition_column: str = "created_at") -> None:
        """Create a weekly partitioned table."""
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {schema_sql}
            )
        """)
        
        # Create index using week extraction
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_week 
            ON {table_name} (strftime('%Y-%W', {partition_column}))
        """)
    
    @staticmethod
    def create_monthly_partition_table(conn: duckdb.DuckDBPyConnection,
                                     table_name: str,
                                     schema_sql: str,
                                     partition_column: str = "created_at") -> None:
        """Create a monthly partitioned table."""
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {schema_sql}
            )
        """)
        
        # Create index using month extraction
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_month 
            ON {table_name} (strftime('%Y-%m', {partition_column}))
        """)
    
    @staticmethod
    def cleanup_old_partitions(conn: duckdb.DuckDBPyConnection,
                             table_name: str,
                             partition_column: str,
                             days_to_keep: int = 30) -> int:
        """
        Clean up old partition data.
        
        Args:
            conn: DuckDB connection
            table_name: Target table
            partition_column: Date column for cleanup
            days_to_keep: Number of days to retain
            
        Returns:
            Number of rows deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        result = conn.execute(f"""
            DELETE FROM {table_name} 
            WHERE {partition_column} < ?
        """, [cutoff_date]).fetchone()
        
        return result[0] if result else 0
    
    @staticmethod
    def get_partition_statistics(conn: duckdb.DuckDBPyConnection,
                               table_name: str,
                               partition_column: str) -> Dict:
        """Get statistics about data distribution across partitions."""
        
        # Daily distribution
        daily_stats = conn.execute(f"""
            SELECT 
                DATE({partition_column}) as partition_date,
                COUNT(*) as row_count,
                AVG(LENGTH(CAST(* AS VARCHAR))) as avg_row_size_bytes
            FROM {table_name}
            GROUP BY DATE({partition_column})
            ORDER BY partition_date DESC
            LIMIT 30
        """).fetchall()
        
        # Weekly distribution  
        weekly_stats = conn.execute(f"""
            SELECT 
                strftime('%Y-%W', {partition_column}) as week,
                COUNT(*) as row_count
            FROM {table_name}
            GROUP BY strftime('%Y-%W', {partition_column})
            ORDER BY week DESC
            LIMIT 12
        """).fetchall()
        
        # Monthly distribution
        monthly_stats = conn.execute(f"""
            SELECT 
                strftime('%Y-%m', {partition_column}) as month,
                COUNT(*) as row_count
            FROM {table_name}
            GROUP BY strftime('%Y-%m', {partition_column})  
            ORDER BY month DESC
            LIMIT 24
        """).fetchall()
        
        return {
            "daily": daily_stats,
            "weekly": weekly_stats,
            "monthly": monthly_stats
        }


class PartitionQueryOptimizer:
    """Optimize queries for partitioned data."""
    
    @staticmethod
    def optimize_date_range_query(table_name: str,
                                partition_column: str,
                                start_date: datetime,
                                end_date: datetime,
                                additional_conditions: str = "") -> str:
        """
        Generate optimized query for date range on partitioned table.
        
        Args:
            table_name: Target table
            partition_column: Date partition column
            start_date: Start of date range
            end_date: End of date range  
            additional_conditions: Additional WHERE conditions
            
        Returns:
            Optimized SQL query
        """
        base_query = f"""
            SELECT * FROM {table_name}
            WHERE {partition_column} >= '{start_date.isoformat()}'
              AND {partition_column} < '{end_date.isoformat()}'
        """
        
        if additional_conditions:
            base_query += f" AND {additional_conditions}"
            
        return base_query
    
    @staticmethod
    def optimize_recent_data_query(table_name: str,
                                 partition_column: str,
                                 hours_back: int = 24,
                                 additional_conditions: str = "") -> str:
        """Generate optimized query for recent data."""
        
        query = f"""
            SELECT * FROM {table_name}
            WHERE {partition_column} >= NOW() - INTERVAL '{hours_back} hours'
        """
        
        if additional_conditions:
            query += f" AND {additional_conditions}"
            
        return query


# Template schemas for common use cases
SCHEMA_TEMPLATES = {
    "hierarchy_events": """
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        level INTEGER NOT NULL,
        parent_id UUID,
        content TEXT NOT NULL,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """,
    
    "system_metrics": """
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        metric_name VARCHAR(100) NOT NULL,
        metric_value DOUBLE NOT NULL,
        metric_unit VARCHAR(20),
        tags JSON,
        hostname VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """,
    
    "application_logs": """
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        level VARCHAR(20) NOT NULL,
        logger VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        exception_info TEXT,
        context_data JSON,
        thread_id VARCHAR(50),
        process_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """,
    
    "rag_events": """
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_text TEXT NOT NULL,
        retrieved_docs JSON,
        response_text TEXT,
        confidence_score DOUBLE,
        processing_time_ms INTEGER,
        embedding_model VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
}


if __name__ == "__main__":
    # Test partitioning templates
    from duckdb_config import get_duckdb_connection
    
    conn = get_duckdb_connection("partitioning_test")
    templates = PartitioningTemplates()
    
    # Create test tables with different partitioning strategies
    print("Creating partitioned tables...")
    
    # Daily partitioned hierarchy events
    templates.create_daily_partition_table(
        conn, "hierarchy_events", SCHEMA_TEMPLATES["hierarchy_events"]
    )
    
    # Weekly partitioned system metrics  
    templates.create_weekly_partition_table(
        conn, "system_metrics", SCHEMA_TEMPLATES["system_metrics"]
    )
    
    # Monthly partitioned application logs
    templates.create_monthly_partition_table(
        conn, "application_logs", SCHEMA_TEMPLATES["application_logs"]
    )
    
    print("Partitioned tables created successfully!")
    
    # Test query optimization
    optimizer = PartitionQueryOptimizer()
    
    recent_query = optimizer.optimize_recent_data_query(
        "system_metrics", "created_at", hours_back=4
    )
    
    print(f"\nOptimized recent data query:\n{recent_query}")
    
    conn.close()