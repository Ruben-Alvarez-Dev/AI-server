#!/usr/bin/env python3
"""
DuckDB Installation Test

Verify DuckDB 0.10.x installation and basic functionality for AI server.
Tests embedded analytical database capabilities for OLAP operations.
"""

import duckdb
import sys
import json

def test_duckdb_installation():
    """Test DuckDB installation and basic operations."""
    
    print("="*60)
    print("DUCKDB INSTALLATION TEST")
    print("="*60)
    
    results = {
        "version": None,
        "connection": False,
        "basic_query": False,
        "table_creation": False,
        "data_insertion": False,
        "analytical_query": False,
        "performance": {}
    }
    
    try:
        # Check version
        version = duckdb.__version__
        results["version"] = version
        print(f"✅ DuckDB version: {version}")
        
        # Test connection
        conn = duckdb.connect(':memory:')
        results["connection"] = True
        print("✅ DuckDB connection established")
        
        # Test basic query
        result = conn.execute("SELECT 'Hello DuckDB' as greeting").fetchone()
        if result[0] == 'Hello DuckDB':
            results["basic_query"] = True
            print("✅ Basic query execution successful")
        
        # Test table creation
        conn.execute("""
            CREATE TABLE test_metrics (
                timestamp TIMESTAMP,
                metric_name VARCHAR,
                metric_value DOUBLE,
                tags MAP(VARCHAR, VARCHAR)
            )
        """)
        results["table_creation"] = True
        print("✅ Table creation successful")
        
        # Test data insertion
        conn.execute("""
            INSERT INTO test_metrics VALUES
            (NOW(), 'cpu_usage', 45.5, MAP {'host': 'server1', 'region': 'us-west'}),
            (NOW() - INTERVAL 1 MINUTE, 'cpu_usage', 42.3, MAP {'host': 'server1', 'region': 'us-west'}),
            (NOW() - INTERVAL 2 MINUTE, 'memory_usage', 78.2, MAP {'host': 'server2', 'region': 'us-east'})
        """)
        results["data_insertion"] = True
        print("✅ Data insertion successful")
        
        # Test analytical query
        import time
        start_time = time.time()
        
        result = conn.execute("""
            SELECT 
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM test_metrics
            GROUP BY metric_name
            ORDER BY avg_value DESC
        """).fetchall()
        
        query_time = (time.time() - start_time) * 1000
        results["analytical_query"] = True
        results["performance"]["analytical_query_ms"] = round(query_time, 2)
        print(f"✅ Analytical query successful ({query_time:.2f}ms)")
        
        # Test extensions availability
        extensions = conn.execute("SELECT * FROM duckdb_extensions()").fetchall()
        available_extensions = [ext[0] for ext in extensions if ext[1]]
        results["available_extensions"] = available_extensions
        print(f"✅ Available extensions: {len(available_extensions)}")
        
        # Test memory settings
        memory_limit = conn.execute("SELECT current_setting('memory_limit')").fetchone()[0]
        results["memory_limit"] = memory_limit
        print(f"✅ Memory limit: {memory_limit}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("INSTALLATION TEST SUMMARY")
        print("="*60)
        
        # Check if version is correct
        if version.startswith('0.10'):
            print(f"✅ Version check: {version} (correct)")
        else:
            print(f"⚠️ Version check: {version} (expected 0.10.x)")
        
        # Overall status
        all_tests = [
            results["connection"],
            results["basic_query"],
            results["table_creation"],
            results["data_insertion"],
            results["analytical_query"]
        ]
        
        if all(all_tests):
            print("✅ All tests passed - DuckDB is ready for AI server operations")
            results["status"] = "SUCCESS"
        else:
            print("❌ Some tests failed - check installation")
            results["status"] = "FAILED"
        
        print("="*60)
        
        # Save results
        with open('/Users/server/Code/AI-projects/AI-server/services/storage/duckdb/installation_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results["status"] == "SUCCESS"
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_duckdb_installation()
    sys.exit(0 if success else 1)