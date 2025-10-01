#!/usr/bin/env python3
"""
Advanced Event Producer with:
- Redis Cluster support
- Distributed tracing
- Multiple traffic patterns (bursty, seasonal, anomalous)
- Circuit breaker pattern
- Adaptive rate limiting
- Event correlation and causality
"""
import os
import time
import json
import random
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
import orjson
from faker import Faker
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configuration
REDIS_CLUSTER = os.getenv("REDIS_CLUSTER", "localhost:7001,localhost:7002,localhost:7003")
PRODUCER_TYPE = os.getenv("PRODUCER_TYPE", "high_frequency")
BASE_RATE = int(os.getenv("RATE", "1000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Prometheus metrics
events_produced = Counter('events_produced_total', 'Total events produced', ['producer_type', 'event_type'])
production_latency = Histogram('production_latency_seconds', 'Event production latency')
batch_size_metric = Histogram('batch_size', 'Batch size distribution')
rate_limiter_drops = Counter('rate_limiter_drops_total', 'Events dropped by rate limiter')
circuit_breaker_state = Gauge('circuit_breaker_open', 'Circuit breaker state (1=open, 0=closed)')

fake = Faker()

@dataclass
class UserSession:
    user_id: str
    session_id: str
    start_time: datetime
    device_type: str
    location: str
    user_agent: str
    is_premium: bool
    
@dataclass
class Event:
    event_id: str
    user_id: str
    session_id: str
    event_type: str
    timestamp: int
    properties: Dict[str, Any]
    trace_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    causality_chain: Optional[List[str]] = None

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                circuit_breaker_state.set(1)
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            circuit_breaker_state.set(0)
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            circuit_breaker_state.set(1 if self.state == "open" else 0)
            raise e

class AdaptiveRateLimiter:
    def __init__(self, base_rate: int):
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = time.time()
    
    def should_allow(self) -> bool:
        now = time.time()
        if now - self.last_adjustment > 10:  # Adjust every 10 seconds
            self._adjust_rate()
            self.last_adjustment = now
        
        # Token bucket algorithm
        return random.random() < (self.current_rate / self.base_rate)
    
    def _adjust_rate(self):
        if self.error_count > self.success_count * 0.1:  # >10% error rate
            self.current_rate = max(self.current_rate * 0.8, self.base_rate * 0.1)
        elif self.error_count < self.success_count * 0.01:  # <1% error rate
            self.current_rate = min(self.current_rate * 1.1, self.base_rate * 2)
        
        self.success_count = 0
        self.error_count = 0

class AdvancedEventProducer:
    def __init__(self):
        self.cluster_nodes = [
            {"host": host.split(":")[0], "port": int(host.split(":")[1])}
            for host in REDIS_CLUSTER.split(",")
        ]
        self.redis_cluster = None
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = AdaptiveRateLimiter(BASE_RATE)
        self.active_sessions: Dict[str, UserSession] = {}
        self.event_correlations: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """Initialize Redis cluster connection"""
        self.redis_cluster = RedisCluster(
            startup_nodes=self.cluster_nodes,
            decode_responses=False,
            skip_full_coverage_check=True,
            health_check_interval=30
        )
        
    def create_user_session(self) -> UserSession:
        """Create a realistic user session"""
        return UserSession(
            user_id=fake.uuid4(),
            session_id=fake.uuid4(),
            start_time=datetime.now(),
            device_type=random.choice(["mobile", "desktop", "tablet"]),
            location=fake.country(),
            user_agent=fake.user_agent(),
            is_premium=random.random() < 0.15  # 15% premium users
        )
    
    def generate_correlated_events(self, session: UserSession) -> List[Event]:
        """Generate realistic event sequences with causality"""
        events = []
        current_time = int(time.time() * 1000)
        
        # Start with page view
        view_event = Event(
            event_id=fake.uuid4(),
            user_id=session.user_id,
            session_id=session.session_id,
            event_type="page_view",
            timestamp=current_time,
            properties={
                "page": random.choice(["/home", "/products", "/search", "/profile"]),
                "referrer": fake.url(),
                "device_type": session.device_type,
                "location": session.location
            }
        )
        events.append(view_event)
        
        # Generate correlated events based on user behavior patterns
        if random.random() < 0.7:  # 70% chance of interaction
            interaction_event = Event(
                event_id=fake.uuid4(),
                user_id=session.user_id,
                session_id=session.session_id,
                event_type=random.choice(["click", "scroll", "hover"]),
                timestamp=current_time + random.randint(1000, 5000),
                properties={
                    "element": random.choice(["button", "link", "image"]),
                    "position": {"x": random.randint(0, 1920), "y": random.randint(0, 1080)}
                },
                parent_event_id=view_event.event_id,
                causality_chain=[view_event.event_id]
            )
            events.append(interaction_event)
            
            # Potential conversion
            if session.is_premium and random.random() < 0.3:
                purchase_event = Event(
                    event_id=fake.uuid4(),
                    user_id=session.user_id,
                    session_id=session.session_id,
                    event_type="purchase",
                    timestamp=current_time + random.randint(5000, 30000),
                    properties={
                        "product_id": fake.uuid4(),
                        "amount": round(random.uniform(10, 500), 2),
                        "currency": "USD",
                        "payment_method": random.choice(["credit_card", "paypal", "apple_pay"])
                    },
                    parent_event_id=interaction_event.event_id,
                    causality_chain=[view_event.event_id, interaction_event.event_id]
                )
                events.append(purchase_event)
        
        return events
    
    def apply_traffic_pattern(self, base_events: List[Event]) -> List[Event]:
        """Apply different traffic patterns based on producer type"""
        if PRODUCER_TYPE == "bursty":
            # Simulate traffic bursts (e.g., flash sales, viral content)
            if random.random() < 0.1:  # 10% chance of burst
                burst_multiplier = random.randint(5, 20)
                return base_events * burst_multiplier
                
        elif PRODUCER_TYPE == "seasonal":
            # Simulate daily/weekly patterns
            hour = datetime.now().hour
            if 9 <= hour <= 17:  # Business hours
                return base_events * 2
            elif 20 <= hour <= 23:  # Evening peak
                return base_events * 3
                
        elif PRODUCER_TYPE == "anomalous":
            # Inject anomalous patterns for ML detection
            if random.random() < 0.05:  # 5% anomalous events
                for event in base_events:
                    event.properties["anomaly_score"] = random.uniform(0.8, 1.0)
                    event.properties["suspicious_pattern"] = True
        
        return base_events
    
    async def produce_batch(self, events: List[Event]) -> bool:
        """Produce a batch of events with distributed tracing"""
        with tracer.start_as_current_span("produce_batch") as span:
            span.set_attribute("batch_size", len(events))
            span.set_attribute("producer_type", PRODUCER_TYPE)
            
            try:
                pipeline = self.redis_cluster.pipeline()
                
                for event in events:
                    # Add trace context
                    event.trace_id = format(span.get_span_context().trace_id, "032x")
                    
                    # Serialize event
                    event_data = orjson.dumps(asdict(event))
                    
                    # Add to appropriate stream based on event type
                    stream_key = f"events:{event.event_type}"
                    pipeline.xadd(stream_key, {"data": event_data})
                    
                    events_produced.labels(
                        producer_type=PRODUCER_TYPE,
                        event_type=event.event_type
                    ).inc()
                
                # Execute batch
                await pipeline.execute()
                batch_size_metric.observe(len(events))
                return True
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise e
    
    async def run(self):
        """Main producer loop with advanced patterns"""
        await self.initialize()
        
        # Start Prometheus metrics server
        start_http_server(8000)
        
        print(f"Advanced Producer ({PRODUCER_TYPE}) starting...")
        print(f"Target rate: {BASE_RATE} events/sec")
        print(f"Batch size: {BATCH_SIZE}")
        
        while True:
            try:
                with tracer.start_as_current_span("production_cycle") as span:
                    start_time = time.time()
                    
                    # Check rate limiter
                    if not self.rate_limiter.should_allow():
                        rate_limiter_drops.inc()
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Generate events
                    events = []
                    for _ in range(BATCH_SIZE):
                        session = self.create_user_session()
                        session_events = self.generate_correlated_events(session)
                        events.extend(self.apply_traffic_pattern(session_events))
                    
                    # Produce with circuit breaker
                    success = await self.circuit_breaker.call(
                        self.produce_batch, events
                    )
                    
                    if success:
                        self.rate_limiter.success_count += len(events)
                    
                    # Rate limiting
                    elapsed = time.time() - start_time
                    target_interval = len(events) / BASE_RATE
                    sleep_time = max(0, target_interval - elapsed)
                    
                    production_latency.observe(elapsed)
                    
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                        
            except Exception as e:
                print(f"Production error: {e}")
                self.rate_limiter.error_count += 1
                await asyncio.sleep(1)

if __name__ == "__main__":
    producer = AdvancedEventProducer()
    asyncio.run(producer.run())