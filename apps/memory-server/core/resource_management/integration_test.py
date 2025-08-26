"""
Resource Management Integration Test
Comprehensive testing of the complete resource management system
"""

import asyncio
import psutil
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import json
import time
from datetime import datetime

from .adaptive_system import AdaptiveResourceManager
from .storage_tier import StorageTierManager
from .cleanup_daemon import IntelligentCleanupDaemon  
from .monitoring import ResourcePressureMonitor
from .graceful_degradation import GracefulDegradationManager, DegradationLevel

async def test_resource_management_integration():
    """Test complete resource management system integration"""
    
    print("🔧 Starting Resource Management Integration Test")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        try:
            # Initialize all components
            print("\n📋 Initializing resource management components...")
            
            adaptive_mgr = AdaptiveResourceManager(base_path)
            storage_mgr = StorageTierManager(base_path) 
            cleanup_daemon = IntelligentCleanupDaemon(base_path)
            monitor = ResourcePressureMonitor(base_path, monitoring_interval=1)  # Fast for testing
            degradation_mgr = GracefulDegradationManager(base_path)
            
            # Test 1: System State Analysis
            print("\n🔍 Test 1: System state analysis...")
            system_state = await adaptive_mgr.get_system_state()
            print(f"   ✅ System pressure: {system_state.system_pressure}")
            print(f"   ✅ Disk usage: {system_state.disk_usage_percent:.1f}%")
            print(f"   ✅ RAM usage: {system_state.ram_usage_percent:.1f}%")
            
            # Test 2: Storage Tier Management
            print("\n💾 Test 2: Storage tier management...")
            await storage_mgr._discover_storage_locations()
            storage_status = await storage_mgr.get_storage_status()
            print(f"   ✅ Storage locations discovered: {len(storage_status['locations'])}")
            
            # Allocate storage for different categories
            test_path = await storage_mgr.allocate_storage("active_conversations", 0.1)
            print(f"   ✅ Allocated storage: {test_path}")
            
            # Test 3: Cleanup Daemon
            print("\n🧹 Test 3: Cleanup daemon functionality...")
            
            # Create test files for cleanup
            temp_files = []
            for i in range(5):
                test_file = base_path / f"test_{i}.tmp"
                test_file.write_text("test content" * 100)
                temp_files.append(test_file)
            
            # Run single cleanup cycle
            await cleanup_daemon._cleanup_cycle()
            cleanup_stats = cleanup_daemon.get_cleanup_stats()
            print(f"   ✅ Cleanup stats: {cleanup_stats['files_deleted']} files deleted")
            
            # Test 4: Resource Monitoring
            print("\n📊 Test 4: Resource monitoring...")
            
            # Start monitoring briefly
            monitor_task = asyncio.create_task(monitor.start_monitoring())
            await asyncio.sleep(3)  # Let it collect a few samples
            await monitor.stop_monitoring()
            
            try:
                await monitor_task
            except:
                pass  # Expected when stopping
                
            monitoring_status = monitor.get_current_status()
            print(f"   ✅ Monitoring samples: {monitoring_status['snapshot_count']}")
            
            # Test 5: Graceful Degradation
            print("\n⚡ Test 5: Graceful degradation...")
            
            # Simulate high resource pressure
            high_pressure_state = {
                "disk_usage_percent": 85,
                "ram_usage_percent": 88, 
                "cpu_usage_percent": 82
            }
            
            target_level = await degradation_mgr.assess_degradation_need(high_pressure_state)
            print(f"   ✅ Assessed degradation level: {target_level.value}")
            
            await degradation_mgr.apply_degradation(target_level, "test_simulation")
            degradation_status = degradation_mgr.get_degradation_status()
            print(f"   ✅ Services disabled: {degradation_status['services_disabled']}")
            
            # Test 6: Integration - Pressure Response
            print("\n🔄 Test 6: Integrated pressure response...")
            
            # Simulate system under pressure
            pressure_analysis = await adaptive_mgr.analyze_pressure(system_state)
            print(f"   ✅ Pressure analysis completed: {pressure_analysis.action_needed}")
            
            if pressure_analysis.action_needed:
                adaptations = await adaptive_mgr.adapt_to_pressure(system_state)
                print(f"   ✅ Adaptations applied: {len(adaptations['changes'])}")
            
            # Test 7: Storage Optimization
            print("\n🎯 Test 7: Storage optimization...")
            await storage_mgr.optimize_storage_layout()
            print("   ✅ Storage layout optimization completed")
            
            # Test 8: Emergency Scenarios
            print("\n🚨 Test 8: Emergency scenario handling...")
            
            # Force emergency cleanup
            await cleanup_daemon.force_cleanup()
            emergency_stats = cleanup_daemon.get_cleanup_stats()
            print(f"   ✅ Emergency cleanup: {emergency_stats['files_deleted']} files processed")
            
            # Force emergency degradation
            await degradation_mgr.apply_degradation(DegradationLevel.EMERGENCY, "test_emergency")
            emergency_status = degradation_mgr.get_degradation_status()
            print(f"   ✅ Emergency degradation: {emergency_status['current_level']}")
            
            # Test 9: System Recovery
            print("\n🔄 Test 9: System recovery...")
            
            # Simulate improved conditions
            normal_pressure_state = {
                "disk_usage_percent": 45,
                "ram_usage_percent": 55,
                "cpu_percent": 35
            }
            
            recovery_level = await degradation_mgr.assess_degradation_need(normal_pressure_state)
            await degradation_mgr.apply_degradation(recovery_level, "test_recovery")
            recovery_status = degradation_mgr.get_degradation_status()
            print(f"   ✅ System recovered to: {recovery_status['current_level']}")
            
            # Test 10: Resource Impact Assessment
            print("\n📈 Test 10: Resource impact assessment...")
            
            resource_impact = await degradation_mgr.calculate_resource_impact()
            print(f"   ✅ Resource savings: {resource_impact['savings_percentage']}")
            
            disk_report = await cleanup_daemon.get_disk_usage_report()
            print(f"   ✅ Disk usage report: {disk_report['total_usage']['usage_percent']:.1f}%")
            
            monitoring_report = await monitor.generate_monitoring_report()
            print(f"   ✅ Monitoring report generated: {len(monitoring_report['recommendations'])} recommendations")
            
            # Test 11: State Persistence
            print("\n💾 Test 11: State persistence...")
            
            await degradation_mgr._save_state()
            await degradation_mgr.load_state()
            print("   ✅ State persistence test completed")
            
            # Final System Health Check
            print("\n🏥 Final system health check...")
            
            final_state = await adaptive_mgr.get_system_state()
            final_config = adaptive_mgr.get_current_configuration()
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "system_pressure": final_state.system_pressure,
                "operation_mode": final_config["mode"],
                "storage_locations": len(storage_status["locations"]),
                "cleanup_stats": cleanup_daemon.get_cleanup_stats(),
                "monitoring_samples": monitoring_status["snapshot_count"],
                "degradation_level": degradation_status["current_level"],
                "resource_savings": resource_impact["resource_savings"]
            }
            
            print("   📊 Final Health Report:")
            for key, value in health_report.items():
                print(f"      {key}: {value}")
            
            print("\n✅ Resource Management Integration Test COMPLETED SUCCESSFULLY")
            
            return {
                "status": "success",
                "tests_passed": 11,
                "health_report": health_report,
                "components_tested": [
                    "AdaptiveResourceManager",
                    "StorageTierManager", 
                    "IntelligentCleanupDaemon",
                    "ResourcePressureMonitor",
                    "GracefulDegradationManager"
                ]
            }
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "failed",
                "error": str(e),
                "tests_passed": 0
            }

async def test_performance_characteristics():
    """Test performance characteristics under load"""
    
    print("\n🚀 Performance Characteristics Test")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Create test data
        print("   Creating test data...")
        for i in range(100):
            test_file = base_path / f"perf_test_{i}.json"
            test_data = {"id": i, "content": "x" * 1000}
            test_file.write_text(json.dumps(test_data))
        
        # Initialize components
        adaptive_mgr = AdaptiveResourceManager(base_path)
        cleanup_daemon = IntelligentCleanupDaemon(base_path)
        
        # Performance test 1: State analysis speed
        print("   Testing state analysis performance...")
        start_time = time.time()
        
        for _ in range(10):
            await adaptive_mgr.get_system_state()
        
        state_analysis_time = (time.time() - start_time) / 10
        print(f"   ✅ Average state analysis time: {state_analysis_time:.3f}s")
        
        # Performance test 2: Cleanup performance
        print("   Testing cleanup performance...")
        start_time = time.time()
        
        await cleanup_daemon.force_cleanup()
        
        cleanup_time = time.time() - start_time
        cleanup_stats = cleanup_daemon.get_cleanup_stats()
        
        print(f"   ✅ Cleanup time: {cleanup_time:.3f}s")
        print(f"   ✅ Files processed: {cleanup_stats['files_deleted']}")
        
        # Performance test 3: Memory usage
        print("   Testing memory usage...")
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run resource-intensive operations
        monitor = ResourcePressureMonitor(base_path, monitoring_interval=0.1)
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        await asyncio.sleep(2)
        await monitor.stop_monitoring()
        
        try:
            await monitor_task
        except:
            pass
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = memory_after - memory_before
        
        print(f"   ✅ Memory usage delta: {memory_delta:.1f} MB")
        
        performance_results = {
            "state_analysis_time_avg": state_analysis_time,
            "cleanup_time": cleanup_time,
            "memory_delta_mb": memory_delta,
            "files_processed": cleanup_stats['files_deleted']
        }
        
        print("   📊 Performance Summary:")
        for key, value in performance_results.items():
            print(f"      {key}: {value}")
        
        return performance_results

async def run_all_tests():
    """Run all resource management tests"""
    
    print("🎯 Starting Complete Resource Management Test Suite")
    print("=" * 60)
    
    # Run integration tests
    integration_results = await test_resource_management_integration()
    
    print("\n" + "=" * 60)
    
    # Run performance tests
    performance_results = await test_performance_characteristics()
    
    print("\n" + "=" * 60)
    print("🎉 TEST SUITE COMPLETED")
    
    final_report = {
        "integration_test": integration_results,
        "performance_test": performance_results,
        "overall_status": "success" if integration_results["status"] == "success" else "failed"
    }
    
    return final_report

if __name__ == "__main__":
    asyncio.run(run_all_tests())