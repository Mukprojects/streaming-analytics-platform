#!/usr/bin/env python3
"""
Advanced Benchmark Suite for Next-Generation Streaming Pipeline
Tests performance, resilience, and advanced features
"""
import asyncio
import time
import json
import statistics
import requests
import redis
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

@dataclass
class BenchmarkResult:
    test_name: str
    duration: float
    throughput: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    additional_metrics: Dict[str, Any]

class AdvancedBenchmark:
    def __init__(self):
        self.redis_cluster = redis.Redis(host='localhost', port=7001, decode_responses=True)
        self.api_url = "http://localhost:8080"
        self.graphql_url = "http://localhost:8080/graphql"
        self.websocket_url = "ws://localhost:8080/ws"
        self.results = []
    
    def test_throughput_scaling(self, duration: int = 60) -> BenchmarkResult:
        """Test throughput scaling under different loads"""
        print(f"🚀 Testing throughput scaling ({duration}s)...")
        
        start_count = self.get_event_count()
        start_time = time.time()
        
        # Monitor for duration
        latencies = []
        error_count = 0
        
        while time.time() - start_time < duration:
            try:
                api_start = time.time()
                response = requests.get(f"{self.api_url}/v2/aggregates", timeout=5)
                latency = time.time() - api_start
                
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    error_count += 1
                    
            except Exception:
                error_count += 1
            
            time.sleep(1)
        
        end_count = self.get_event_count()
        actual_duration = time.time() - start_time
        
        events_processed = end_count - start_count
        throughput = events_processed / actual_duration
        error_rate = error_count / len(latencies) if latencies else 1.0
        
        return BenchmarkResult(
            test_name="throughput_scaling",
            duration=actual_duration,
            throughput=throughput,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0,
            error_rate=error_rate,
            additional_metrics={
                "events_processed": events_processed,
                "api_requests": len(latencies),
                "errors": error_count
            }
        )
    
    def test_graphql_performance(self, num_requests: int = 100) -> BenchmarkResult:
        """Test GraphQL API performance"""
        print(f"📊 Testing GraphQL performance ({num_requests} requests)...")
        
        query = """
        query {
            aggregates {
                totalEvents
                eventsByType
                lastUpdated
            }
            realTimeMetrics {
                currentThroughput
                avgLatency
                errorRate
                activeUsers
            }
        }
        """
        
        latencies = []
        error_count = 0
        start_time = time.time()
        
        for _ in range(num_requests):
            try:
                request_start = time.time()
                response = requests.post(
                    self.graphql_url,
                    json={"query": query},
                    timeout=10
                )
                latency = time.time() - request_start
                
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    error_count += 1
                    
            except Exception:
                error_count += 1
        
        duration = time.time() - start_time
        
        return BenchmarkResult(
            test_name="graphql_performance",
            duration=duration,
            throughput=len(latencies) / duration,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0,
            error_rate=error_count / num_requests,
            additional_metrics={
                "total_requests": num_requests,
                "successful_requests": len(latencies),
                "errors": error_count
            }
        )
    
    def test_concurrent_load(self, concurrent_users: int = 50, requests_per_user: int = 20) -> BenchmarkResult:
        """Test system under concurrent load"""
        print(f"⚡ Testing concurrent load ({concurrent_users} users, {requests_per_user} req/user)...")
        
        def user_session(user_id: int) -> List[float]:
            """Simulate a user session with multiple requests"""
            session_latencies = []
            
            for _ in range(requests_per_user):
                try:
                    start = time.time()
                    response = requests.get(f"{self.api_url}/v2/aggregates", timeout=10)
                    latency = time.time() - start
                    
                    if response.status_code == 200:
                        session_latencies.append(latency)
                    
                    # Random delay between requests
                    time.sleep(np.random.exponential(0.1))
                    
                except Exception:
                    pass
            
            return session_latencies
        
        start_time = time.time()
        all_latencies = []
        error_count = 0
        
        # Execute concurrent user sessions
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_session, user_id) 
                for user_id in range(concurrent_users)
            ]
            
            for future in as_completed(futures):
                try:
                    latencies = future.result()
                    all_latencies.extend(latencies)
                except Exception:
                    error_count += 1
        
        duration = time.time() - start_time
        total_requests = concurrent_users * requests_per_user
        
        return BenchmarkResult(
            test_name="concurrent_load",
            duration=duration,
            throughput=len(all_latencies) / duration,
            latency_p50=statistics.median(all_latencies) if all_latencies else 0,
            latency_p95=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 20 else 0,
            latency_p99=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) > 100 else 0,
            error_rate=error_count / concurrent_users,
            additional_metrics={
                "concurrent_users": concurrent_users,
                "total_requests": total_requests,
                "successful_requests": len(all_latencies),
                "failed_sessions": error_count
            }
        )
    
    def test_cache_performance(self, num_requests: int = 200) -> BenchmarkResult:
        """Test caching system performance"""
        print(f"💾 Testing cache performance ({num_requests} requests)...")
        
        # First, warm up the cache
        requests.get(f"{self.api_url}/v2/aggregates?use_cache=true")
        
        cached_latencies = []
        uncached_latencies = []
        
        # Test cached requests
        for _ in range(num_requests // 2):
            try:
                start = time.time()
                response = requests.get(f"{self.api_url}/v2/aggregates?use_cache=true")
                latency = time.time() - start
                
                if response.status_code == 200:
                    cached_latencies.append(latency)
            except Exception:
                pass
        
        # Test uncached requests
        for _ in range(num_requests // 2):
            try:
                start = time.time()
                response = requests.get(f"{self.api_url}/v2/aggregates?use_cache=false")
                latency = time.time() - start
                
                if response.status_code == 200:
                    uncached_latencies.append(latency)
            except Exception:
                pass
        
        all_latencies = cached_latencies + uncached_latencies
        cache_speedup = (
            statistics.mean(uncached_latencies) / statistics.mean(cached_latencies)
            if cached_latencies and uncached_latencies else 1.0
        )
        
        return BenchmarkResult(
            test_name="cache_performance",
            duration=0,  # Not time-based test
            throughput=0,
            latency_p50=statistics.median(all_latencies) if all_latencies else 0,
            latency_p95=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 20 else 0,
            latency_p99=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) > 100 else 0,
            error_rate=0,
            additional_metrics={
                "cached_avg_latency": statistics.mean(cached_latencies) if cached_latencies else 0,
                "uncached_avg_latency": statistics.mean(uncached_latencies) if uncached_latencies else 0,
                "cache_speedup": cache_speedup,
                "cached_requests": len(cached_latencies),
                "uncached_requests": len(uncached_latencies)
            }
        )
    
    def test_resilience_under_chaos(self, duration: int = 120) -> BenchmarkResult:
        """Test system resilience during chaos experiments"""
        print(f"🔥 Testing resilience under chaos ({duration}s)...")
        
        start_time = time.time()
        latencies = []
        error_count = 0
        
        # Monitor system during chaos experiments
        while time.time() - start_time < duration:
            try:
                request_start = time.time()
                response = requests.get(f"{self.api_url}/health", timeout=5)
                latency = time.time() - request_start
                
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    error_count += 1
                    
            except Exception:
                error_count += 1
            
            time.sleep(2)  # Check every 2 seconds
        
        actual_duration = time.time() - start_time
        total_checks = len(latencies) + error_count
        
        return BenchmarkResult(
            test_name="chaos_resilience",
            duration=actual_duration,
            throughput=0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0,
            error_rate=error_count / total_checks if total_checks > 0 else 1.0,
            additional_metrics={
                "total_health_checks": total_checks,
                "successful_checks": len(latencies),
                "failed_checks": error_count,
                "availability": len(latencies) / total_checks if total_checks > 0 else 0
            }
        )
    
    def get_event_count(self) -> int:
        """Get current total event count"""
        try:
            count = self.redis_cluster.hget("aggregates", "total_count")
            return int(count) if count else 0
        except Exception:
            return 0
    
    def generate_report(self):
        """Generate comprehensive benchmark report"""
        print("\n" + "="*80)
        print("🎯 ADVANCED STREAMING PIPELINE BENCHMARK REPORT")
        print("="*80)
        
        for result in self.results:
            print(f"\n📊 {result.test_name.upper().replace('_', ' ')}")
            print("-" * 50)
            
            if result.throughput > 0:
                print(f"Throughput: {result.throughput:.1f} req/sec")
            
            if result.latency_p50 > 0:
                print(f"Latency P50: {result.latency_p50*1000:.1f}ms")
                print(f"Latency P95: {result.latency_p95*1000:.1f}ms")
                print(f"Latency P99: {result.latency_p99*1000:.1f}ms")
            
            print(f"Error Rate: {result.error_rate*100:.2f}%")
            
            # Additional metrics
            for key, value in result.additional_metrics.items():
                if isinstance(value, float):
                    print(f"{key.replace('_', ' ').title()}: {value:.3f}")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Overall system assessment
        print(f"\n🏆 OVERALL SYSTEM ASSESSMENT")
        print("-" * 50)
        
        avg_throughput = statistics.mean([r.throughput for r in self.results if r.throughput > 0])
        avg_latency = statistics.mean([r.latency_p95 for r in self.results if r.latency_p95 > 0])
        avg_error_rate = statistics.mean([r.error_rate for r in self.results])
        
        print(f"Average Throughput: {avg_throughput:.1f} req/sec")
        print(f"Average P95 Latency: {avg_latency*1000:.1f}ms")
        print(f"Average Error Rate: {avg_error_rate*100:.2f}%")
        
        # Performance grade
        grade = self.calculate_performance_grade(avg_throughput, avg_latency, avg_error_rate)
        print(f"Performance Grade: {grade}")
        
        # Save detailed results
        with open("advanced_benchmark_results.json", "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        print(f"\n📁 Detailed results saved to: advanced_benchmark_results.json")
    
    def calculate_performance_grade(self, throughput: float, latency: float, error_rate: float) -> str:
        """Calculate overall performance grade"""
        score = 0
        
        # Throughput scoring (0-40 points)
        if throughput >= 100:
            score += 40
        elif throughput >= 50:
            score += 30
        elif throughput >= 20:
            score += 20
        else:
            score += 10
        
        # Latency scoring (0-40 points)
        if latency <= 0.05:  # 50ms
            score += 40
        elif latency <= 0.1:  # 100ms
            score += 30
        elif latency <= 0.2:  # 200ms
            score += 20
        else:
            score += 10
        
        # Error rate scoring (0-20 points)
        if error_rate <= 0.01:  # 1%
            score += 20
        elif error_rate <= 0.05:  # 5%
            score += 15
        elif error_rate <= 0.1:  # 10%
            score += 10
        else:
            score += 5
        
        # Grade assignment
        if score >= 90:
            return "A+ (Google-Ready)"
        elif score >= 80:
            return "A (Production-Ready)"
        elif score >= 70:
            return "B+ (Near Production)"
        elif score >= 60:
            return "B (Good Performance)"
        else:
            return "C (Needs Improvement)"
    
    def run_all_tests(self):
        """Run complete benchmark suite"""
        print("🚀 Starting Advanced Benchmark Suite...")
        print("This will test throughput, latency, concurrency, caching, and resilience")
        print("-" * 80)
        
        # Run all benchmark tests
        tests = [
            lambda: self.test_throughput_scaling(60),
            lambda: self.test_graphql_performance(100),
            lambda: self.test_concurrent_load(25, 10),
            lambda: self.test_cache_performance(200),
            lambda: self.test_resilience_under_chaos(60)
        ]
        
        for i, test in enumerate(tests, 1):
            print(f"\n[{i}/{len(tests)}] Running test...")
            try:
                result = test()
                self.results.append(result)
                print(f"✅ {result.test_name} completed")
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Generate comprehensive report
        self.generate_report()

if __name__ == "__main__":
    benchmark = AdvancedBenchmark()
    benchmark.run_all_tests()