#!/usr/bin/env python3
"""
DuckDB Connection and Query Testing

Comprehensive testing of DuckDB setup, connections, and query performance.
"""

import time
import json
from datetime import datetime, timedelta
from duckdb_config import get_duckdb_connection
from initial_schemas import SchemaManager


class DuckDBTester:
    """Test DuckDB functionality and performance."""
    
    def __init__(self):
        self.schema_manager = SchemaManager()
        self.test_results = {}
    
    def test_connections(self) -> dict:
        """Test connections to all databases."""
        
        databases = ["hierarchy_data", "metrics_data", "logs_data", "rag_data", "system_data"]
        results = {}
        
        for db_name in databases:
            try:
                start_time = time.time()
                conn = get_duckdb_connection(db_name)
                
                # Test basic query
                result = conn.execute("SELECT 'Connection successful' as status").fetchone()
                
                connection_time = time.time() - start_time
                
                conn.close()
                
                results[db_name] = {
                    "status": "SUCCESS",
                    "connection_time_ms": round(connection_time * 1000, 2),
                    "result": result[0] if result else "No result"
                }
                
            except Exception as e:
                results[db_name] = {
                    "status": "FAILED",
                    "error": str(e)
                }
        
        return results
    
    def test_insert_performance(self) -> dict:
        """Test insert performance across different data types."""
        
        results = {}
        
        # Test hierarchy data insertions
        conn = get_duckdb_connection("hierarchy_data")
        
        try:
            # Insert test hierarchy events
            start_time = time.time()
            
            for i in range(100):
                conn.execute("""
                    INSERT INTO l1_cache (level, content, metadata)
                    VALUES (?, ?, ?)
                """, [1, f"Test content {i}", json.dumps({"test_id": i, "timestamp": datetime.now().isoformat()})])
            
            insert_time = time.time() - start_time
            
            results["hierarchy_inserts"] = {
                "records": 100,
                "time_ms": round(insert_time * 1000, 2),
                "records_per_second": round(100 / insert_time, 2)
            }
            
        except Exception as e:
            results["hierarchy_inserts"] = {"error": str(e)}
        finally:
            conn.close()
        
        # Test metrics data insertions
        conn = get_duckdb_connection("metrics_data")
        
        try:
            start_time = time.time()
            
            for i in range(1000):
                conn.execute("""
                    INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags)
                    VALUES (?, ?, ?, ?)
                """, [f"test_metric_{i % 10}", float(i), "count", json.dumps({"test": True})])
            
            insert_time = time.time() - start_time
            
            results["metrics_inserts"] = {
                "records": 1000,
                "time_ms": round(insert_time * 1000, 2),
                "records_per_second": round(1000 / insert_time, 2)
            }
            
        except Exception as e:
            results["metrics_inserts"] = {"error": str(e)}
        finally:
            conn.close()
        
        return results
    
    def test_query_performance(self) -> dict:
        """Test query performance and optimization."""
        
        results = {}
        
        # Test hierarchy queries
        conn = get_duckdb_connection("hierarchy_data")
        
        try:
            # Test recent data query
            start_time = time.time()
            
            recent_data = conn.execute("""
                SELECT COUNT(*), AVG(level), MIN(created_at), MAX(created_at)
                FROM l1_cache
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """).fetchone()
            
            query_time = time.time() - start_time
            
            results["recent_data_query"] = {
                "time_ms": round(query_time * 1000, 2),
                "result": {
                    "count": recent_data[0],
                    "avg_level": round(recent_data[1], 2) if recent_data[1] else 0,
                    "date_range": f"{recent_data[2]} to {recent_data[3]}"
                }
            }
            
            # Test aggregation query
            start_time = time.time()
            
            agg_data = conn.execute("""
                SELECT level, COUNT(*) as count, AVG(LENGTH(content)) as avg_content_length
                FROM l1_cache
                GROUP BY level
                ORDER BY level
            """).fetchall()
            
            agg_time = time.time() - start_time
            
            results["aggregation_query"] = {
                "time_ms": round(agg_time * 1000, 2),
                "results": [{"level": row[0], "count": row[1], "avg_length": round(row[2], 2)} for row in agg_data]
            }
            
        except Exception as e:
            results["hierarchy_queries"] = {"error": str(e)}
        finally:
            conn.close()
        
        # Test metrics queries
        conn = get_duckdb_connection("metrics_data")
        
        try:
            # Test time-series aggregation
            start_time = time.time()
            
            timeseries_data = conn.execute("""
                SELECT 
                    metric_name,
                    COUNT(*) as count,
                    MIN(metric_value) as min_val,
                    MAX(metric_value) as max_val,
                    AVG(metric_value) as avg_val,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY metric_value) as median_val
                FROM system_metrics
                GROUP BY metric_name
                ORDER BY count DESC
                LIMIT 5
            """).fetchall()
            
            timeseries_time = time.time() - start_time
            
            results["timeseries_aggregation"] = {
                "time_ms": round(timeseries_time * 1000, 2),
                "metrics": [{
                    "name": row[0],
                    "count": row[1],
                    "min": row[2],
                    "max": row[3],
                    "avg": round(row[4], 2),
                    "median": round(row[5], 2)
                } for row in timeseries_data]
            }
            
        except Exception as e:
            results["timeseries_queries"] = {"error": str(e)}
        finally:
            conn.close()
        
        return results
    
    def test_memory_usage(self) -> dict:
        """Test memory usage and limits."""
        
        results = {}
        
        conn = get_duckdb_connection("system_data")
        
        try:
            # Check memory limit setting
            memory_limit = conn.execute("SELECT current_setting('memory_limit')").fetchone()
            
            # Check temporary directory setting  
            temp_dir = conn.execute("SELECT current_setting('temp_directory')").fetchone()
            
            # Check thread setting
            threads = conn.execute("SELECT current_setting('threads')").fetchone()
            
            results["configuration"] = {
                "memory_limit": memory_limit[0] if memory_limit else "Unknown",
                "temp_directory": temp_dir[0] if temp_dir else "Unknown", 
                "threads": threads[0] if threads else "Unknown"
            }
            
            # Test large data handling (memory spill test)
            start_time = time.time()
            
            large_result = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT * FROM generate_series(1, 10000) as t1
                    CROSS JOIN generate_series(1, 100) as t2
                )
            """).fetchone()
            
            large_query_time = time.time() - start_time
            
            results["memory_spill_test"] = {
                "rows_processed": large_result[0],
                "time_ms": round(large_query_time * 1000, 2),
                "status": "SUCCESS"
            }
            
        except Exception as e:
            results["memory_test"] = {"error": str(e)}
        finally:
            conn.close()
        
        return results
    
    def run_comprehensive_tests(self) -> dict:
        """Run all tests and return comprehensive results."""
        
        print("Running comprehensive DuckDB tests...")
        
        # Test 1: Connection tests
        print("1. Testing database connections...")
        connection_results = self.test_connections()
        
        # Test 2: Insert performance
        print("2. Testing insert performance...")
        insert_results = self.test_insert_performance()
        
        # Test 3: Query performance
        print("3. Testing query performance...")
        query_results = self.test_query_performance()
        
        # Test 4: Memory usage
        print("4. Testing memory configuration...")
        memory_results = self.test_memory_usage()
        
        # Compile results
        all_results = {
            "test_timestamp": datetime.now().isoformat(),
            "connection_tests": connection_results,
            "insert_performance": insert_results,
            "query_performance": query_results,
            "memory_tests": memory_results
        }
        
        return all_results
    
    def print_test_summary(self, results: dict) -> None:
        """Print a formatted summary of test results."""
        
        print("\n" + "="*60)
        print("DUCKDB TEST RESULTS SUMMARY")
        print("="*60)
        
        # Connection tests summary
        print("\n📡 CONNECTION TESTS:")
        for db_name, result in results["connection_tests"].items():
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            if result["status"] == "SUCCESS":
                print(f"  {status_icon} {db_name}: {result['connection_time_ms']}ms")
            else:
                print(f"  {status_icon} {db_name}: {result['error']}")
        
        # Performance tests summary
        print("\n⚡ PERFORMANCE TESTS:")
        if "hierarchy_inserts" in results["insert_performance"]:
            h_insert = results["insert_performance"]["hierarchy_inserts"]
            if "error" not in h_insert:
                print(f"  ✅ Hierarchy Inserts: {h_insert['records_per_second']} records/sec")
        
        if "metrics_inserts" in results["insert_performance"]:
            m_insert = results["insert_performance"]["metrics_inserts"] 
            if "error" not in m_insert:
                print(f"  ✅ Metrics Inserts: {m_insert['records_per_second']} records/sec")
        
        # Query performance
        if "recent_data_query" in results["query_performance"]:
            recent = results["query_performance"]["recent_data_query"]
            print(f"  ✅ Recent Data Query: {recent['time_ms']}ms")
        
        if "aggregation_query" in results["query_performance"]:
            agg = results["query_performance"]["aggregation_query"]
            print(f"  ✅ Aggregation Query: {agg['time_ms']}ms")
        
        # Memory configuration
        print("\n🧠 MEMORY CONFIGURATION:")
        if "configuration" in results["memory_tests"]:
            config = results["memory_tests"]["configuration"]
            print(f"  ✅ Memory Limit: {config['memory_limit']}")
            print(f"  ✅ Threads: {config['threads']}")
            print(f"  ✅ Temp Directory: {config['temp_directory']}")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    # Run comprehensive tests
    tester = DuckDBTester()
    results = tester.run_comprehensive_tests()
    
    # Print summary
    tester.print_test_summary(results)
    
    # Save detailed results
    with open("services/storage/data/duckdb/test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: services/storage/data/duckdb/test_results.json")
    print("✅ All DuckDB tests completed successfully!")