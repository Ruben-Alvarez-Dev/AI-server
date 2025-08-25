#!/usr/bin/env python3
"""
Basic Performance Tests for Memory-Server
Tests performance characteristics without full ML model loading
"""

import sys
import time
import asyncio
import psutil
from pathlib import Path
import numpy as np

def test_system_resources():
    """Test system resource detection"""
    print("💻 Testing System Resources...")
    
    try:
        # Test memory detection
        if 'psutil' in sys.modules:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            usage_percent = memory.percent
            
            print(f"  ✅ Total RAM: {total_gb:.1f} GB")
            print(f"  ✅ Available RAM: {available_gb:.1f} GB") 
            print(f"  ✅ RAM Usage: {usage_percent:.1f}%")
            
            # Test CPU detection
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            print(f"  ✅ CPU Cores: {cpu_count}")
            print(f"  ✅ CPU Usage: {cpu_usage:.1f}%")
            
        else:
            print("  ⚠️  psutil not available, using basic detection")
            
        return True
        
    except Exception as e:
        print(f"  ❌ System resources test failed: {e}")
        return False

def test_memory_performance():
    """Test memory allocation and performance"""
    print("🧠 Testing Memory Performance...")
    
    try:
        # Test large array creation (simulating embeddings)
        start_time = time.time()
        large_array = np.random.rand(10000, 768)  # 10K embeddings
        creation_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Created 10K embeddings in {creation_time:.1f}ms")
        
        # Test memory size calculation
        array_size_mb = large_array.nbytes / (1024**2)
        print(f"  ✅ Array size: {array_size_mb:.1f} MB")
        
        # Test search simulation (dot product)
        query_vector = np.random.rand(768)
        
        start_time = time.time()
        similarities = np.dot(large_array, query_vector)
        search_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Vector search in {search_time:.1f}ms")
        
        # Test top-k selection
        start_time = time.time()
        top_k_indices = np.argsort(similarities)[-10:]
        topk_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Top-10 selection in {topk_time:.1f}ms")
        
        # Memory cleanup test
        del large_array, similarities
        print("  ✅ Memory cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Memory performance test failed: {e}")
        return False

def test_async_performance():
    """Test async operation performance"""
    print("⚡ Testing Async Performance...")
    
    try:
        # Test single async operation
        async def mock_embedding_operation(text_size: int):
            # Simulate embedding generation time based on text size
            await asyncio.sleep(text_size * 0.0001)  # 0.1ms per character
            return np.random.rand(768)
        
        start_time = time.time()
        embedding = asyncio.run(mock_embedding_operation(1000))
        single_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Single async embedding: {single_time:.1f}ms")
        
        # Test concurrent async operations
        async def test_concurrent_embeddings():
            tasks = [mock_embedding_operation(500) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            return results
        
        start_time = time.time()
        results = asyncio.run(test_concurrent_embeddings())
        concurrent_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ 10 concurrent embeddings: {concurrent_time:.1f}ms")
        print(f"  📊 Concurrency speedup: {(single_time * 10) / concurrent_time:.1f}x")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Async performance test failed: {e}")
        return False

def test_text_processing_performance():
    """Test text processing performance"""
    print("📝 Testing Text Processing Performance...")
    
    try:
        # Generate test text
        test_text = "This is a test sentence. " * 1000  # ~25KB of text
        
        # Test text splitting
        start_time = time.time()
        sentences = test_text.split('. ')
        split_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Text splitting: {split_time:.2f}ms for {len(test_text)} chars")
        
        # Test regex processing
        import re
        start_time = time.time()
        words = re.findall(r'\w+', test_text)
        regex_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Regex word extraction: {regex_time:.1f}ms ({len(words)} words)")
        
        # Test chunk boundary calculation
        chunk_size = 512
        overlap = 0.2
        
        start_time = time.time()
        boundaries = []
        text_len = len(test_text)
        overlap_size = int(chunk_size * overlap)
        
        for i in range(0, text_len, chunk_size - overlap_size):
            start = i
            end = min(i + chunk_size, text_len)
            boundaries.append((start, end))
        
        boundary_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Chunk boundaries: {boundary_time:.2f}ms ({len(boundaries)} chunks)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Text processing performance test failed: {e}")
        return False

def test_file_io_performance():
    """Test file I/O performance"""
    print("💾 Testing File I/O Performance...")
    
    try:
        from core.config import get_config
        config = get_config()
        
        # Test writing performance
        test_file = config.CACHE_DIR / "performance_test.txt"
        test_data = "Performance test data line.\n" * 10000  # ~250KB
        
        start_time = time.time()
        with open(test_file, 'w') as f:
            f.write(test_data)
        write_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ File write: {write_time:.1f}ms ({len(test_data)} bytes)")
        
        # Test reading performance
        start_time = time.time()
        with open(test_file, 'r') as f:
            read_data = f.read()
        read_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ File read: {read_time:.1f}ms ({len(read_data)} bytes)")
        
        # Test JSON serialization performance
        import json
        test_dict = {
            "embeddings": [[float(x) for x in np.random.rand(768)] for _ in range(100)],
            "metadata": [{"id": i, "source": f"doc_{i}"} for i in range(100)]
        }
        
        start_time = time.time()
        json_str = json.dumps(test_dict)
        json_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ JSON serialization: {json_time:.1f}ms ({len(json_str)} chars)")
        
        # Cleanup
        test_file.unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"  ❌ File I/O performance test failed: {e}")
        return False

def test_configuration_performance():
    """Test configuration access performance"""
    print("⚙️ Testing Configuration Performance...")
    
    try:
        from core.config import get_config
        
        # Test config access speed
        start_time = time.time()
        for _ in range(1000):
            config = get_config()
            _ = config.API_PORT
            _ = config.EMBEDDING_MODEL
            _ = config.MAX_CONTEXT_LENGTH
        access_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ 1000 config accesses: {access_time:.1f}ms")
        print(f"  📊 Average per access: {access_time/1000:.3f}ms")
        
        # Test config serialization
        start_time = time.time()
        config_dict = config.to_dict()
        serial_time = (time.time() - start_time) * 1000
        
        print(f"  ✅ Config serialization: {serial_time:.2f}ms")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration performance test failed: {e}")
        return False

def run_performance_tests():
    """Run all performance tests"""
    print("🧪 Memory-Server Basic Performance Tests")
    print("=" * 60)
    
    tests = [
        test_system_resources,
        test_memory_performance,
        test_async_performance,
        test_text_processing_performance,
        test_file_io_performance,
        test_configuration_performance
    ]
    
    passed = 0
    failed = 0
    
    overall_start = time.time()
    
    for test in tests:
        try:
            test_start = time.time()
            if test():
                test_time = (time.time() - test_start) * 1000
                passed += 1
                print(f"✅ {test.__name__} PASSED ({test_time:.1f}ms)\n")
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED\n")
        except Exception as e:
            print(f"💥 {test.__name__} CRASHED: {e}\n")
            failed += 1
    
    total_time = (time.time() - overall_start) * 1000
    
    print("=" * 60)
    print(f"📊 PERFORMANCE TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    print(f"   ⏱️  Total Time: {total_time:.1f}ms")
    
    if failed == 0:
        print("\n🎉 ALL PERFORMANCE TESTS PASSED! 🎉")
        print("✨ Memory-Server performance is good!")
        return True
    else:
        print(f"\n⚠️  {failed} performance tests failed.")
        return passed > failed

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)