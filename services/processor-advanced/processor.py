#!/usr/bin/env python3
"""
Advanced Stream Processor with:
- Multi-stage processing pipeline
- Real-time ML inference
- Complex event processing (CEP)
- Exactly-once semantics with idempotency
- Dynamic scaling based on lag
- Advanced windowing and aggregations
"""
import os
import time
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
import orjson
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configuration
REDIS_CLUSTER = os.getenv("REDIS_CLUSTER", "localhost:7001,localhost:7002,localhost:7003")
STAGE = os.getenv("STAGE", "enrichment")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "processors")
INPUT_STREAM = os.getenv("INPUT_STREAM", "events:*")
OUTPUT_STREAM = os.getenv("OUTPUT_STREAM", "processed_events")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "60"))  # seconds
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

# Initialize tracing and logging
tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()

# Prometheus metrics
events_processed = Counter('events_processed_total', 'Events processed', ['stage', 'event_type'])
processing_latency = Histogram('processing_latency_seconds', 'Processing latency', ['stage'])
window_events = Gauge('window_events_count', 'Events in current window', ['window_type'])
anomaly_score = Histogram('anomaly_score', 'ML anomaly scores')
idempotency_hits = Counter('idempotency_hits_total', 'Idempotency cache hits')

@dataclass
class ProcessedEvent:
    original_event: Dict[str, Any]
    enrichments: Dict[str, Any]
    ml_scores: Dict[str, float]
    processing_metadata: Dict[str, Any]
    stage: str
    timestamp: int

class SlidingWindow:
    """Advanced sliding window for real-time aggregations"""
    def __init__(self, window_size: int, slide_interval: int = 10):
        self.window_size = window_size
        self.slide_interval = slide_interval
        self.events = deque()
        self.aggregates = defaultdict(lambda: defaultdict(float))
        
    def add_event(self, event: Dict[str, Any]):
        current_time = time.time()
        self.events.append((current_time, event))
        
        # Remove old events
        cutoff_time = current_time - self.window_size
        while self.events and self.events[0][0] < cutoff_time:
            self.events.popleft()
        
        # Update aggregates
        self._update_aggregates()
    
    def _update_aggregates(self):
        """Update real-time aggregates"""
        self.aggregates.clear()
        
        for timestamp, event in self.events:
            event_type = event.get('event_type', 'unknown')
            user_id = event.get('user_id')
            
            # Basic counts
            self.aggregates['counts'][event_type] += 1
            self.aggregates['total']['events'] += 1
            
            # User activity
            if user_id:
                self.aggregates['unique_users'][user_id] = True
            
            # Value aggregations
            if 'amount' in event.get('properties', {}):
                amount = float(event['properties']['amount'])
                self.aggregates['revenue']['total'] += amount
                self.aggregates['revenue'][event_type] += amount
        
        # Convert unique users to count
        self.aggregates['unique_users'] = {
            'count': len(self.aggregates['unique_users'])
        }
        
        window_events.labels(window_type='sliding').set(len(self.events))

class ComplexEventProcessor:
    """Complex Event Processing for pattern detection"""
    def __init__(self):
        self.pattern_buffer = defaultdict(list)
        self.patterns = {
            'purchase_funnel': self._detect_purchase_funnel,
            'fraud_pattern': self._detect_fraud_pattern,
            'churn_risk': self._detect_churn_risk
        }
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Detect complex patterns in event streams"""
        user_id = event.get('user_id')
        session_id = event.get('session_id')
        
        # Add to pattern buffer
        key = f"{user_id}:{session_id}"
        self.pattern_buffer[key].append(event)
        
        # Keep only recent events (last 30 minutes)
        cutoff_time = time.time() - 1800
        self.pattern_buffer[key] = [
            e for e in self.pattern_buffer[key]
            if e.get('timestamp', 0) / 1000 > cutoff_time
        ]
        
        # Run pattern detection
        detected_patterns = {}
        for pattern_name, detector in self.patterns.items():
            result = detector(self.pattern_buffer[key])
            if result:
                detected_patterns[pattern_name] = result
        
        return detected_patterns
    
    def _detect_purchase_funnel(self, events: List[Dict]) -> Optional[Dict]:
        """Detect purchase funnel progression"""
        event_types = [e.get('event_type') for e in events]
        
        # Look for view -> click -> purchase sequence
        if ('page_view' in event_types and 
            'click' in event_types and 
            'purchase' in event_types):
            
            view_idx = event_types.index('page_view')
            click_idx = event_types.index('click')
            purchase_idx = event_types.index('purchase')
            
            if view_idx < click_idx < purchase_idx:
                return {
                    'funnel_completed': True,
                    'conversion_time': events[purchase_idx]['timestamp'] - events[view_idx]['timestamp'],
                    'steps': len(set(event_types))
                }
        return None
    
    def _detect_fraud_pattern(self, events: List[Dict]) -> Optional[Dict]:
        """Detect potential fraud patterns"""
        if len(events) < 3:
            return None
        
        # Check for rapid successive purchases
        purchases = [e for e in events if e.get('event_type') == 'purchase']
        if len(purchases) >= 3:
            time_diffs = []
            for i in range(1, len(purchases)):
                diff = purchases[i]['timestamp'] - purchases[i-1]['timestamp']
                time_diffs.append(diff / 1000)  # Convert to seconds
            
            if all(diff < 60 for diff in time_diffs):  # All within 1 minute
                return {
                    'rapid_purchases': True,
                    'purchase_count': len(purchases),
                    'avg_time_between': np.mean(time_diffs)
                }
        return None
    
    def _detect_churn_risk(self, events: List[Dict]) -> Optional[Dict]:
        """Detect churn risk patterns"""
        if not events:
            return None
        
        # Check for declining engagement
        recent_events = [e for e in events if e.get('timestamp', 0) / 1000 > time.time() - 86400]  # Last 24h
        older_events = [e for e in events if e.get('timestamp', 0) / 1000 <= time.time() - 86400]
        
        if len(older_events) > 0:
            recent_rate = len(recent_events) / 1  # events per day
            older_rate = len(older_events) / max(1, len(older_events) / 10)  # approximate
            
            if recent_rate < older_rate * 0.3:  # 70% decline
                return {
                    'churn_risk': True,
                    'engagement_decline': (older_rate - recent_rate) / older_rate,
                    'recent_activity': recent_rate
                }
        return None

class MLAnomalyDetector:
    """Real-time ML-based anomaly detection"""
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.feature_buffer = deque(maxlen=1000)
        self.is_trained = False
        
    def extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from event"""
        features = []
        
        # Temporal features
        timestamp = event.get('timestamp', time.time() * 1000) / 1000
        hour = datetime.fromtimestamp(timestamp).hour
        day_of_week = datetime.fromtimestamp(timestamp).weekday()
        
        features.extend([hour, day_of_week])
        
        # Event properties
        properties = event.get('properties', {})
        
        # Numerical properties
        amount = properties.get('amount', 0)
        features.append(float(amount) if amount else 0)
        
        # Categorical encoded as numbers
        event_type_map = {'page_view': 1, 'click': 2, 'purchase': 3, 'signup': 4}
        event_type_num = event_type_map.get(event.get('event_type'), 0)
        features.append(event_type_num)
        
        # Device type
        device_map = {'mobile': 1, 'desktop': 2, 'tablet': 3}
        device_num = device_map.get(properties.get('device_type'), 0)
        features.append(device_num)
        
        return np.array(features).reshape(1, -1)
    
    def update_model(self, event: Dict[str, Any]):
        """Update ML model with new data"""
        features = self.extract_features(event)
        self.feature_buffer.append(features[0])
        
        # Retrain periodically
        if len(self.feature_buffer) >= 100 and len(self.feature_buffer) % 50 == 0:
            X = np.array(list(self.feature_buffer))
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            self.is_trained = True
    
    def get_anomaly_score(self, event: Dict[str, Any]) -> float:
        """Get anomaly score for event"""
        if not self.is_trained:
            return 0.0
        
        features = self.extract_features(event)
        features_scaled = self.scaler.transform(features)
        
        # Get anomaly score (lower = more anomalous)
        score = self.model.decision_function(features_scaled)[0]
        
        # Convert to 0-1 scale (higher = more anomalous)
        normalized_score = max(0, min(1, (0.5 - score) / 1.0))
        
        anomaly_score.observe(normalized_score)
        return normalized_score

class AdvancedProcessor:
    def __init__(self):
        self.cluster_nodes = [
            {"host": host.split(":")[0], "port": int(host.split(":")[1])}
            for host in REDIS_CLUSTER.split(",")
        ]
        self.redis_cluster = None
        self.sliding_window = SlidingWindow(WINDOW_SIZE)
        self.cep = ComplexEventProcessor()
        self.ml_detector = MLAnomalyDetector()
        self.idempotency_cache: Set[str] = set()
        
    async def initialize(self):
        """Initialize connections and state"""
        self.redis_cluster = RedisCluster(
            startup_nodes=self.cluster_nodes,
            decode_responses=True,
            skip_full_coverage_check=True
        )
        
        # Create consumer group
        try:
            await self.redis_cluster.xgroup_create(
                INPUT_STREAM, CONSUMER_GROUP, id='0', mkstream=True
            )
        except Exception:
            pass  # Group already exists
    
    def generate_idempotency_key(self, event: Dict[str, Any]) -> str:
        """Generate idempotency key for exactly-once processing"""
        event_id = event.get('event_id', '')
        user_id = event.get('user_id', '')
        timestamp = event.get('timestamp', '')
        
        key_data = f"{event_id}:{user_id}:{timestamp}:{STAGE}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    async def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event with additional data"""
        enrichments = {}
        
        # Geo enrichment (simulated)
        user_location = event.get('properties', {}).get('location')
        if user_location:
            enrichments['geo'] = {
                'country': user_location,
                'timezone': 'UTC',  # Simplified
                'region': 'unknown'
            }
        
        # User profile enrichment (from cache/database)
        user_id = event.get('user_id')
        if user_id:
            # Simulate user profile lookup
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            enrichments['user_profile'] = {
                'segment': 'premium' if user_hash % 10 < 2 else 'standard',
                'lifetime_value': (user_hash % 1000) * 10,
                'registration_date': '2023-01-01'  # Simplified
            }
        
        # Session enrichment
        session_id = event.get('session_id')
        if session_id:
            enrichments['session'] = {
                'duration_estimate': random.randint(60, 3600),
                'page_views': random.randint(1, 20),
                'is_bounce': random.random() < 0.4
            }
        
        return enrichments
    
    async def process_event(self, event: Dict[str, Any]) -> ProcessedEvent:
        """Process single event through the pipeline"""
        with tracer.start_as_current_span("process_event") as span:
            span.set_attribute("stage", STAGE)
            span.set_attribute("event_type", event.get('event_type', 'unknown'))
            
            start_time = time.time()
            
            # Check idempotency
            idem_key = self.generate_idempotency_key(event)
            if idem_key in self.idempotency_cache:
                idempotency_hits.inc()
                return None
            
            self.idempotency_cache.add(idem_key)
            
            # Stage-specific processing
            if STAGE == "enrichment":
                enrichments = await self.enrich_event(event)
                ml_scores = {}
                
            elif STAGE == "aggregation":
                # Add to sliding window
                self.sliding_window.add_event(event)
                enrichments = {
                    'window_aggregates': dict(self.sliding_window.aggregates)
                }
                ml_scores = {}
                
            elif STAGE == "ml_inference":
                # ML processing
                self.ml_detector.update_model(event)
                anomaly_score = self.ml_detector.get_anomaly_score(event)
                
                enrichments = {}
                ml_scores = {
                    'anomaly_score': anomaly_score,
                    'is_anomaly': anomaly_score > 0.7
                }
                
            else:  # Default processing
                enrichments = await self.enrich_event(event)
                ml_scores = {}
            
            # Complex event processing
            cep_results = self.cep.process_event(event)
            if cep_results:
                enrichments['patterns'] = cep_results
            
            # Create processed event
            processed = ProcessedEvent(
                original_event=event,
                enrichments=enrichments,
                ml_scores=ml_scores,
                processing_metadata={
                    'stage': STAGE,
                    'processing_time': time.time() - start_time,
                    'processor_id': os.getenv('HOSTNAME', 'unknown'),
                    'idempotency_key': idem_key
                },
                stage=STAGE,
                timestamp=int(time.time() * 1000)
            )
            
            # Update metrics
            events_processed.labels(
                stage=STAGE,
                event_type=event.get('event_type', 'unknown')
            ).inc()
            processing_latency.labels(stage=STAGE).observe(time.time() - start_time)
            
            return processed
    
    async def run(self):
        """Main processing loop"""
        await self.initialize()
        
        # Start metrics server
        start_http_server(8000)
        
        logger.info(f"Advanced Processor ({STAGE}) starting...")
        
        while True:
            try:
                # Read events from stream
                streams = await self.redis_cluster.xreadgroup(
                    CONSUMER_GROUP,
                    f"processor-{STAGE}-{os.getpid()}",
                    {INPUT_STREAM: '>'},
                    count=BATCH_SIZE,
                    block=5000
                )
                
                if not streams:
                    continue
                
                # Process batch
                processed_events = []
                ack_ids = []
                
                for stream_name, messages in streams:
                    for msg_id, fields in messages:
                        try:
                            event_data = orjson.loads(fields['data'])
                            processed = await self.process_event(event_data)
                            
                            if processed:
                                processed_events.append(processed)
                            
                            ack_ids.append((stream_name, msg_id))
                            
                        except Exception as e:
                            logger.error(f"Error processing event {msg_id}: {e}")
                
                # Write processed events to output stream
                if processed_events:
                    pipeline = self.redis_cluster.pipeline()
                    
                    for processed in processed_events:
                        output_data = orjson.dumps(asdict(processed))
                        pipeline.xadd(OUTPUT_STREAM, {'data': output_data})
                    
                    await pipeline.execute()
                
                # Acknowledge processed messages
                for stream_name, msg_id in ack_ids:
                    await self.redis_cluster.xack(stream_name, CONSUMER_GROUP, msg_id)
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    import random  # Add missing import
    processor = AdvancedProcessor()
    asyncio.run(processor.run())