#!/usr/bin/env python3
"""
Advanced Chaos Engineering Service
Implements Netflix's Chaos Monkey principles for distributed systems testing
"""
import os
import time
import random
import docker
import schedule
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Gauge, start_http_server

# Configuration
CHAOS_INTERVAL = int(os.getenv("CHAOS_INTERVAL", "300"))  # 5 minutes
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.1"))  # 10% failure rate
TARGET_SERVICES = os.getenv("TARGET_SERVICES", "producer-high-freq,processor-stage1,processor-stage2").split(",")

# Initialize logging
logger = structlog.get_logger()

# Prometheus metrics
chaos_experiments = Counter('chaos_experiments_total', 'Total chaos experiments', ['experiment_type', 'target_service'])
service_failures = Counter('service_failures_induced', 'Service failures induced', ['service', 'failure_type'])
recovery_time = Gauge('service_recovery_time_seconds', 'Service recovery time', ['service'])

class ChaosExperiment:
    """Base class for chaos experiments"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
    
    async def execute(self, target_service: str) -> Dict[str, Any]:
        """Execute the chaos experiment"""
        raise NotImplementedError
    
    def get_results(self) -> Dict[str, Any]:
        """Get experiment results"""
        return {
            'name': self.name,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (self.end_time - self.start_time) if self.end_time and self.start_time else None
        }

class ServiceKillExperiment(ChaosExperiment):
    """Kill a service container and measure recovery time"""
    def __init__(self):
        super().__init__(
            "service_kill",
            "Randomly kill service containers to test recovery mechanisms"
        )
    
    async def execute(self, target_service: str) -> Dict[str, Any]:
        self.start_time = time.time()
        
        try:
            client = docker.from_env()
            
            # Find containers for the target service
            containers = client.containers.list(
                filters={'label': f'com.docker.compose.service={target_service}'}
            )
            
            if not containers:
                logger.warning(f"No containers found for service: {target_service}")
                return {'success': False, 'reason': 'No containers found'}
            
            # Kill a random container
            target_container = random.choice(containers)
            container_name = target_container.name
            
            logger.info(f"Killing container: {container_name}")
            target_container.kill()
            
            service_failures.labels(service=target_service, failure_type='kill').inc()
            
            # Wait for recovery
            recovery_start = time.time()
            max_wait = 120  # 2 minutes max wait
            
            while time.time() - recovery_start < max_wait:
                time.sleep(5)
                
                # Check if service is back up
                new_containers = client.containers.list(
                    filters={'label': f'com.docker.compose.service={target_service}'}
                )
                
                healthy_containers = [
                    c for c in new_containers 
                    if c.status == 'running'
                ]
                
                if healthy_containers:
                    recovery_duration = time.time() - recovery_start
                    recovery_time.labels(service=target_service).set(recovery_duration)
                    
                    logger.info(f"Service {target_service} recovered in {recovery_duration:.2f}s")
                    
                    self.end_time = time.time()
                    return {
                        'success': True,
                        'killed_container': container_name,
                        'recovery_time': recovery_duration
                    }
            
            logger.error(f"Service {target_service} failed to recover within {max_wait}s")
            self.end_time = time.time()
            return {'success': False, 'reason': 'Recovery timeout'}
            
        except Exception as e:
            logger.error(f"Error in service kill experiment: {e}")
            self.end_time = time.time()
            return {'success': False, 'reason': str(e)}

class NetworkPartitionExperiment(ChaosExperiment):
    """Simulate network partitions between services"""
    def __init__(self):
        super().__init__(
            "network_partition",
            "Create network partitions to test distributed system resilience"
        )
    
    async def execute(self, target_service: str) -> Dict[str, Any]:
        self.start_time = time.time()
        
        try:
            client = docker.from_env()
            
            # Find containers for the target service
            containers = client.containers.list(
                filters={'label': f'com.docker.compose.service={target_service}'}
            )
            
            if not containers:
                return {'success': False, 'reason': 'No containers found'}
            
            target_container = random.choice(containers)
            
            logger.info(f"Creating network partition for: {target_container.name}")
            
            # Pause container (simulates network partition)
            target_container.pause()
            
            service_failures.labels(service=target_service, failure_type='network_partition').inc()
            
            # Wait for partition duration
            partition_duration = random.randint(10, 60)  # 10-60 seconds
            time.sleep(partition_duration)
            
            # Resume container
            target_container.unpause()
            
            logger.info(f"Network partition resolved for: {target_container.name}")
            
            self.end_time = time.time()
            return {
                'success': True,
                'partition_duration': partition_duration,
                'affected_container': target_container.name
            }
            
        except Exception as e:
            logger.error(f"Error in network partition experiment: {e}")
            self.end_time = time.time()
            return {'success': False, 'reason': str(e)}

class ResourceExhaustionExperiment(ChaosExperiment):
    """Simulate resource exhaustion (CPU/Memory stress)"""
    def __init__(self):
        super().__init__(
            "resource_exhaustion",
            "Stress test services with high CPU/memory usage"
        )
    
    async def execute(self, target_service: str) -> Dict[str, Any]:
        self.start_time = time.time()
        
        try:
            client = docker.from_env()
            
            containers = client.containers.list(
                filters={'label': f'com.docker.compose.service={target_service}'}
            )
            
            if not containers:
                return {'success': False, 'reason': 'No containers found'}
            
            target_container = random.choice(containers)
            
            logger.info(f"Starting resource stress test on: {target_container.name}")
            
            # Execute stress command inside container
            stress_command = "python -c \"import time; [x**2 for x in range(1000000)] while True\""
            
            # Run stress test for limited time
            exec_result = target_container.exec_run(
                f"timeout 30 {stress_command}",
                detach=True
            )
            
            service_failures.labels(service=target_service, failure_type='resource_stress').inc()
            
            # Monitor for 30 seconds
            time.sleep(30)
            
            logger.info(f"Resource stress test completed for: {target_container.name}")
            
            self.end_time = time.time()
            return {
                'success': True,
                'stress_duration': 30,
                'affected_container': target_container.name
            }
            
        except Exception as e:
            logger.error(f"Error in resource exhaustion experiment: {e}")
            self.end_time = time.time()
            return {'success': False, 'reason': str(e)}

class ChaosMonkey:
    """Main chaos engineering orchestrator"""
    def __init__(self):
        self.experiments = [
            ServiceKillExperiment(),
            NetworkPartitionExperiment(),
            ResourceExhaustionExperiment()
        ]
        self.experiment_history = []
    
    def should_run_experiment(self) -> bool:
        """Determine if an experiment should run based on failure rate"""
        return random.random() < FAILURE_RATE
    
    async def run_random_experiment(self):
        """Run a random chaos experiment"""
        if not self.should_run_experiment():
            logger.info("Skipping chaos experiment (probability check)")
            return
        
        # Select random experiment and target
        experiment = random.choice(self.experiments)
        target_service = random.choice(TARGET_SERVICES)
        
        logger.info(f"Starting chaos experiment: {experiment.name} on {target_service}")
        
        # Record experiment
        chaos_experiments.labels(
            experiment_type=experiment.name,
            target_service=target_service
        ).inc()
        
        # Execute experiment
        result = await experiment.execute(target_service)
        
        # Store results
        experiment_record = {
            **experiment.get_results(),
            'target_service': target_service,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        self.experiment_history.append(experiment_record)
        
        # Keep only last 100 experiments
        if len(self.experiment_history) > 100:
            self.experiment_history = self.experiment_history[-100:]
        
        logger.info(f"Chaos experiment completed: {experiment.name} - {result}")
    
    def get_experiment_stats(self) -> Dict[str, Any]:
        """Get statistics about chaos experiments"""
        if not self.experiment_history:
            return {'total_experiments': 0}
        
        total = len(self.experiment_history)
        successful = sum(1 for exp in self.experiment_history if exp['result'].get('success', False))
        
        experiment_types = {}
        for exp in self.experiment_history:
            exp_type = exp['name']
            if exp_type not in experiment_types:
                experiment_types[exp_type] = {'total': 0, 'successful': 0}
            
            experiment_types[exp_type]['total'] += 1
            if exp['result'].get('success', False):
                experiment_types[exp_type]['successful'] += 1
        
        return {
            'total_experiments': total,
            'successful_experiments': successful,
            'success_rate': successful / total if total > 0 else 0,
            'experiment_types': experiment_types,
            'last_experiment': self.experiment_history[-1] if self.experiment_history else None
        }
    
    def start_scheduler(self):
        """Start the chaos experiment scheduler"""
        logger.info(f"Starting Chaos Monkey with {CHAOS_INTERVAL}s interval")
        logger.info(f"Target services: {TARGET_SERVICES}")
        logger.info(f"Failure rate: {FAILURE_RATE}")
        
        # Schedule regular chaos experiments
        schedule.every(CHAOS_INTERVAL).seconds.do(
            lambda: asyncio.create_task(self.run_random_experiment())
        )
        
        # Start metrics server
        start_http_server(8000)
        
        # Main loop
        while True:
            schedule.run_pending()
            time.sleep(10)

if __name__ == "__main__":
    import asyncio
    
    chaos_monkey = ChaosMonkey()
    
    try:
        chaos_monkey.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Chaos Monkey stopped by user")
    except Exception as e:
        logger.error(f"Chaos Monkey error: {e}")