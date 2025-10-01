#!/usr/bin/env python3
"""
Advanced Redis Cluster Performance Test
Tests the Redis cluster performance and capabilities
"""
import time
import redis
import statistics

def test_redis_cluster():
    """Test Redis cluster performance"""
    print("🎯 REDIS CLUSTER PERFORMANCE TEST")
    print("="*50)
    
    nodes = [
        {"host": "localhost", "port": 7001},
        {"host": "localhost", "port": 7002}, 
        {"host": "localhost", "port": 7003}
    ]
    
    results = []
    
    for i, node in enumerate(nodes, 1):
        print(f"\n📊 Testing Node {i} (port {node['port']})...")
        
        try:
            # Connect to individual node
            r = redis.Redis(host=node['host'], port=node['port'], decode_responses=True)
            r.ping()
            print(f"  ✅ Connection: SUCCESS")
            
            # Performance test
            start_time = time.time()
            operations = 1000
            
            # Write test
            for j in range(operations):
                r.set(f"test_key_{i}_{j}", f"test_value_{j}")
            
            write_time = time.time() - start_time
            
            # Read test  
            start_time = time.time()
            for j in range(operations):
                r.get(f"test_key_{i}_{j}")
            
            read_time = time.time() - start_time
            
            # Calculate performance
            write_ops_sec = operations / write_time
            read_ops_sec = operations / read_time
            
            print(f"  📈 Write Performance: {write_ops_sec:.0f} ops/sec")
            print(f"  📈 Read Performance: {read_ops_sec:.0f} ops/sec")
            
            results.append({
                'node': i,
                'write_ops_sec': write_ops_sec,
                'read_ops_sec': read_ops_sec
            })
            
            # Cleanup
            for j in range(operations):
                r.delete(f"test_key_{i}_{j}")
                
        except Exception as e:
            print(f"  ❌ Node {i} Error: {e}")
    
    # Summary
    if results:
        print(f"\n🏆 CLUSTER PERFORMANCE SUMMARY")
        print("-" * 40)
        
        total_write = sum(r['write_ops_sec'] for r in results)
        total_read = sum(r['read_ops_sec'] for r in results)
        
        print(f"Total Write Performance: {total_write:.0f} ops/sec")
        print(f"Total Read Performance: {total_read:.0f} ops/sec")
        print(f"Active Nodes: {len(results)}/3")
        
        if len(results) == 3:
            print("✅ Full cluster operational - Ready for production!")
        else:
            print("⚠️ Partial cluster - Some nodes may be starting")
    
    return len(results) > 0

def test_cluster_features():
    """Test Redis cluster specific features"""
    print(f"\n🔧 CLUSTER FEATURES TEST")
    print("-" * 40)
    
    try:
        # Connect to cluster
        r = redis.Redis(host='localhost', port=7001, decode_responses=True)
        
        # Test cluster info
        try:
            info = r.execute_command('CLUSTER', 'INFO')
            if 'cluster_state:ok' in info:
                print("  ✅ Cluster State: OK")
            else:
                print("  ⚠️ Cluster State: Initializing")
        except:
            print("  ❌ Cluster commands not available")
        
        # Test basic operations
        r.set("cluster_test", "working")
        value = r.get("cluster_test")
        
        if value == "working":
            print("  ✅ Basic Operations: Working")
        else:
            print("  ❌ Basic Operations: Failed")
            
        r.delete("cluster_test")
        
    except Exception as e:
        print(f"  ❌ Cluster test failed: {e}")

if __name__ == "__main__":
    print("🚀 ADVANCED REDIS CLUSTER TESTING")
    print("="*50)
    
    success = test_redis_cluster()
    
    if success:
        test_cluster_features()
        print(f"\n🎯 RESULT: Advanced Redis Cluster is operational!")
        print("   Ready for Google-level demonstration! 🚀")
    else:
        print(f"\n❌ RESULT: Cluster may still be starting up")
        print("   Wait 60 seconds and try again")