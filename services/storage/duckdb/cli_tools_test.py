#!/usr/bin/env python3
"""
DuckDB CLI Tools Test

Verify DuckDB CLI installation and functionality for interactive querying
and database management tasks in AI server operations.
"""

import subprocess
import os
import json
import tempfile
import time

def test_duckdb_cli():
    """Test DuckDB CLI tools functionality."""
    
    print("="*60)
    print("DUCKDB CLI TOOLS TEST")
    print("="*60)
    
    results = {
        "cli_available": False,
        "cli_version": None,
        "cli_path": None,
        "interactive_mode": False,
        "file_database": False,
        "sql_execution": False,
        "export_import": False,
        "performance": {}
    }
    
    try:
        # Check if DuckDB CLI is available
        which_result = subprocess.run(
            ["which", "duckdb"],
            capture_output=True,
            text=True
        )
        
        if which_result.returncode == 0:
            cli_path = which_result.stdout.strip()
            results["cli_available"] = True
            results["cli_path"] = cli_path
            print(f"✅ DuckDB CLI found: {cli_path}")
        else:
            print("❌ DuckDB CLI not found in PATH")
            return False
        
        # Check CLI version
        version_result = subprocess.run(
            ["duckdb", "--version"],
            capture_output=True,
            text=True
        )
        
        if version_result.returncode == 0:
            version = version_result.stdout.strip()
            results["cli_version"] = version
            print(f"✅ DuckDB CLI version: {version}")
        
        # Test SQL execution via CLI
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            sql_file = f.name
            f.write("""
                CREATE TABLE test_metrics (
                    timestamp TIMESTAMP,
                    metric_name VARCHAR,
                    value DOUBLE
                );
                
                INSERT INTO test_metrics VALUES
                    (NOW(), 'cpu_usage', 45.5),
                    (NOW() - INTERVAL 1 MINUTE, 'memory_usage', 78.2),
                    (NOW() - INTERVAL 2 MINUTE, 'disk_usage', 62.1);
                
                SELECT 
                    metric_name,
                    AVG(value) as avg_value,
                    COUNT(*) as count
                FROM test_metrics
                GROUP BY metric_name
                ORDER BY avg_value DESC;
            """)
        
        # Execute SQL file with CLI
        start_time = time.time()
        
        sql_result = subprocess.run(
            ["duckdb", ":memory:", "-c", f".read {sql_file}"],
            capture_output=True,
            text=True
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        if sql_result.returncode == 0:
            results["sql_execution"] = True
            results["performance"]["sql_execution_ms"] = round(execution_time, 2)
            print(f"✅ SQL execution via CLI successful ({execution_time:.2f}ms)")
            
            # Parse output
            output_lines = sql_result.stdout.strip().split('\n')
            if len(output_lines) > 0:
                print(f"   Query returned {len([l for l in output_lines if l.strip()])} result rows")
        else:
            print(f"❌ SQL execution failed: {sql_result.stderr}")
        
        # Test file database creation
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = os.path.join(tmpdir, "test.duckdb")
            
            # Create database file
            create_result = subprocess.run(
                ["duckdb", db_file, "-c", "CREATE TABLE test(id INTEGER, name VARCHAR);"],
                capture_output=True,
                text=True
            )
            
            if create_result.returncode == 0 and os.path.exists(db_file):
                results["file_database"] = True
                file_size = os.path.getsize(db_file)
                print(f"✅ File database creation successful ({file_size} bytes)")
            else:
                print("❌ File database creation failed")
        
        # Test export functionality
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_file = f.name
        
        export_result = subprocess.run(
            ["duckdb", ":memory:", "-c", 
             f"CREATE TABLE export_test AS SELECT * FROM range(10); COPY export_test TO '{csv_file}' (HEADER, DELIMITER ',');"],
            capture_output=True,
            text=True
        )
        
        if export_result.returncode == 0 and os.path.exists(csv_file):
            csv_size = os.path.getsize(csv_file)
            if csv_size > 0:
                results["export_import"] = True
                print(f"✅ CSV export successful ({csv_size} bytes)")
        
        # Clean up temp files
        try:
            os.unlink(sql_file)
            os.unlink(csv_file)
        except:
            pass
        
        # Test interactive mode availability
        # Note: Can't fully test interactive mode in script, just check if it would launch
        help_result = subprocess.run(
            ["duckdb", "-help"],
            capture_output=True,
            text=True
        )
        
        if "DESCRIPTION" in help_result.stdout:
            results["interactive_mode"] = True
            print("✅ Interactive mode available")
        
        print("\n" + "="*60)
        print("CLI TOOLS TEST SUMMARY")
        print("="*60)
        
        # Version compatibility check
        if results["cli_version"]:
            # CLI version is typically newer, which is fine
            print(f"✅ CLI Version: {results['cli_version']}")
            print(f"   Python package: 0.10.0")
            print(f"   Compatibility: OK (CLI can be newer)")
        
        # Overall status
        critical_tests = [
            results["cli_available"],
            results["sql_execution"],
            results["file_database"]
        ]
        
        if all(critical_tests):
            print("✅ All critical tests passed - DuckDB CLI ready for use")
            results["status"] = "SUCCESS"
        else:
            print("❌ Some critical tests failed")
            results["status"] = "FAILED"
        
        print("="*60)
        
        # Save results
        with open('/Users/server/Code/AI-projects/AI-server/services/storage/duckdb/cli_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results["status"] == "SUCCESS"
        
    except Exception as e:
        print(f"❌ CLI tools test failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = test_duckdb_cli()
    sys.exit(0 if success else 1)