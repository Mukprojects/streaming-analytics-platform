#!/usr/bin/env python3
"""
Advanced chaos testing for the streaming pipeline.
Tests various failure scenarios and recovery patterns.
"""
import time
import subprocess
import requests
import redis
import json
import threading
from datetime import datetime

class ChaosTest:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.api_url = "http://localhost:8080"
        self.results = []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def get_metrics(self):
        """Get current system metrics"""
        try:
            # Get event count
            total_events = self.redis_client.hget("aggregates", "total_count") or "0"
            
            # Get API status
            api_response = requests.get(f"{self.api_url}/health", timeout=5)
            api_healthy = api_response.status_code == 200
            
            return {
                "timestamp": time.time(),
                "total_events": int(total_events),
                "api_healthy": api_healthy
            }
        except Exception as e:
            return {
                "timestamp": time.time(),
                "total_events": 0,
                "api_healthy": False,
                "error": str(e)
            }
    
    def docker_command(self, cmd):
        """Execute docker-compose command"""
        try:
            result = subprocess.run(
                f"docker-compose {cmd}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def test_processor_crash(self):
        """Test processor crash and recovery"""
        self.log("Starting processor crash test...")
        
        # Record baseline
        baseline = self.get_metrics()
        self.log(f"Baseline: {baseline['total_events']} events")
        
        # Stop processor
        self.log("Stopping processor...")
        success, stdout, stderr = self.docker_command("stop processor")
        if not success:
            self.log(f"Failed to stop processor: {stderr}")
            return False
        
        # Wait and monitor
        downtime_start = time.time()
        self.log("Monitoring during downtime (15s)...")
        time.sleep(15)
        
        # Restart processor
        self.log("Restarting processor...")
        success, stdout, stderr = self.docker_command("start processor")
        if not success:
            self.log(f"Failed to restart processor: {stderr}")
            return False
        
        # Monitor recovery
        self.log("Monitoring recovery (10s)...")
        time.sleep(10)
        
        # Check final state
        final = self.get_metrics()
        events_during_test = final['total_events'] - baseline['total_events']
        
        self.log(f"Recovery complete. Events processed during test: {events_during_test}")
        
        return {
            "test": "processor_crash",
            "baseline_events": baseline['total_events'],
            "final_events": final['total_events'],
            "events_during_test": events_during_test,
            "downtime_seconds": 15,
            "success": events_during_test > 0
        }
    
    def test_redis_network_partition(self):
        """Simulate Redis network issues"""
        self.log("Starting Redis network partition test...")
        
        baseline = self.get_metrics()
        
        # Pause Redis container (simulates network partition)
        self.log("Pausing Redis container...")
        success, stdout, stderr = self.docker_command("pause redis")
        if not success:
            self.log(f"Failed to pause Redis: {stderr}")
            return False
        
        # Wait during partition
        self.log("Network partition active (10s)...")
        time.sleep(10)
        
        # Resume Redis
        self.log("Resuming Redis...")
        success, stdout, stderr = self.docker_command("unpause redis")
        if not success:
            self.log(f"Failed to unpause Redis: {stderr}")
            return False
        
        # Monitor recovery
        self.log("Monitoring recovery (15s)...")
        time.sleep(15)
        
        final = self.get_metrics()
        
        return {
            "test": "redis_partition",
            "baseline_events": baseline['total_events'],
            "final_events": final['total_events'],
            "partition_seconds": 10,
            "recovery_observed": final['api_healthy']
        }
    
    def run_all_tests(self):
        """Run all chaos tests"""
        self.log("=== Starting Chaos Testing Suite ===")
        
        tests = [
            self.test_processor_crash,
            self.test_redis_network_partition
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                if result:
                    self.results.append(result)
                    self.log(f"Test completed: {result.get('test', 'unknown')}")
                else:
                    self.log(f"Test failed: {test_func.__name__}")
                
                # Wait between tests
                self.log("Waiting 30s before next test...")
                time.sleep(30)
                
            except Exception as e:
                self.log(f"Test error in {test_func.__name__}: {e}")
        
        # Save results
        with open("chaos_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log("=== Chaos Testing Complete ===")
        self.log(f"Results saved to chaos_test_results.json")
        
        return self.results

if __name__ == "__main__":
    chaos = ChaosTest()
    results = chaos.run_all_tests()
    
    print("\n=== Summary ===")
    for result in results:
        print(f"Test: {result.get('test', 'unknown')}")
        print(f"Success: {result.get('success', 'unknown')}")
        print("-" * 30)