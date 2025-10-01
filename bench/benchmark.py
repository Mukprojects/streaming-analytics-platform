#!/usr/bin/env python3
"""
Comprehensive benchmark script for the streaming pipeline.
Measures throughput, latency, and system performance.
"""
import time
import redis
import os
import json
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
AGG_KEY = os.getenv("AGG_KEY", "aggregates")
API_URL = os.getenv("API_URL", "http://localhost:8080")
DURATION = int(os.getenv("DURATION", "60"))  # seconds

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

class BenchmarkResults:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_count = 0
        self.end_count = 0
        self.api_latencies = []
        self.errors = 0

def get_total_count():
    """Get current total event count from aggregates"""
    try:
        v = r.hget(AGG_KEY, "total_count")
        return int(v) if v else 0
    except:
        return 0

def test_api_latency(results, stop_event):
    """Continuously test API response times"""
    while not stop_event.is_set():
        try:
            start = time.time()
            response = requests.get(f"{API_URL}/aggregates/summary", timeout=5)
            latency = time.time() - start
            
            if response.status_code == 200:
                results.api_latencies.append(latency)
            else:
                results.errors += 1
                
        except Exception:
            results.errors += 1
            
        time.sleep(1)

def run_benchmark():
    """Run comprehensive benchmark"""
    print(f"Starting {DURATION}s benchmark...")
    print(f"Redis: {REDIS_HOST}")
    print(f"API: {API_URL}")
    print("-" * 50)
    
    results = BenchmarkResults()
    stop_event = threading.Event()
    
    # Start API latency testing in background
    api_thread = threading.Thread(
        target=test_api_latency, 
        args=(results, stop_event)
    )
    api_thread.start()
    
    # Record initial state
    results.start_time = time.time()
    results.start_count = get_total_count()
    
    print(f"Initial event count: {results.start_count}")
    
    # Wait for benchmark duration
    time.sleep(DURATION)
    
    # Record final state
    results.end_time = time.time()
    results.end_count = get_total_count()
    
    # Stop API testing
    stop_event.set()
    api_thread.join()
    
    # Calculate results
    elapsed = results.end_time - results.start_time
    events_processed = results.end_count - results.start_count
    throughput = events_processed / elapsed if elapsed > 0 else 0
    
    print(f"\nBenchmark Results ({elapsed:.1f}s):")
    print(f"Events processed: {events_processed:,}")
    print(f"Throughput: {throughput:.1f} events/sec")
    
    if results.api_latencies:
        print(f"\nAPI Performance:")
        print(f"  Requests: {len(results.api_latencies)}")
        print(f"  Errors: {results.errors}")
        print(f"  Avg latency: {statistics.mean(results.api_latencies)*1000:.1f}ms")
        print(f"  95th percentile: {statistics.quantiles(results.api_latencies, n=20)[18]*1000:.1f}ms")
    
    return {
        "duration": elapsed,
        "events_processed": events_processed,
        "throughput": throughput,
        "api_requests": len(results.api_latencies),
        "api_errors": results.errors,
        "avg_api_latency": statistics.mean(results.api_latencies) if results.api_latencies else 0
    }

if __name__ == "__main__":
    try:
        results = run_benchmark()
        
        # Save results to file
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to benchmark_results.json")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted")
    except Exception as e:
        print(f"Benchmark error: {e}")