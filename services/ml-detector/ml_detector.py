#!/usr/bin/env python3
"""
ML-Powered Anomaly Detection Service
Real-time anomaly detection using Isolation Forest and custom algorithms
"""
import os
import time
import json
import asyncio
import pickle
from typing import Dict, List, Any, Optional
from collections import deque
import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
import orjson
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configuration
REDIS_CLUSTER = os.getenv("REDIS_CLUSTER", "localhost:7001,localhost:7002,localhost:7003")
MODEL_PATH = os.getenv("MODEL_PATH", "/models/anomaly_detector.pkl")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "ml_detectors")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", f"ml-detector-{os.getpid()}")

# Initialize logging and tracing
logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

# Prometheus metrics
anomalies_detected = Counter('anomalies_detected_total', 'Total anomalies detected', ['anomaly_type'])
ml_inference_latency = Histogram('ml_inference_latency_seconds', 'ML inference latency')
model_accuracy = Gauge('model_accuracy_score', 'Current model accuracy estimate')
events_analyzed = Counter('events_analyzed_total', 'Total events analyzed by ML')

class AdvancedAnomalyDetector:
    """Advanced ML-based anomaly detection with multiple algorithms"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        
        self.feature_buffer = deque(maxlen=10000)
        self.anomaly_buffer = deque(maxlen=1000)
        self.is_trained = False
        self.model_version = 1
        
        # Behavioral baselines
        self.user_baselines = {}
        self.global_baseline = {
            'avg_session_length': 300,
            'avg_events_per_session': 10,
            'avg_purchase_amount': 50.0
        }
    
    def extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """Extract comprehensive features from event"""
        features = []
        
        # Temporal features
        timestamp = event.get('timestamp', time.time() * 1000) / 1000
        dt = pd.to_datetime(timestamp, unit='s')
        
        features.extend([
            dt.hour,
            dt.weekday(),
            dt.minute,
            timestamp % 86400,  # seconds since midnight
        ])
        
        # Event properties
        properties = event.get('properties', {})
        
        # Numerical features
        amount = properties.get('amount', 0)
        features.append(float(amount) if amount else 0)
        
        # Categorical features (encoded)
        event_type_map = {
            'page_view': 1, 'click': 2, 'purchase': 3, 
            'signup': 4, 'logout': 5, 'search': 6
        }
        features.append(event_type_map.get(event.get('event_type'), 0))
        
        device_map = {'mobile': 1, 'desktop': 2, 'tablet': 3}
        features.append(device_map.get(properties.get('device_type'), 0))
        
        # User behavior features
        user_id = event.get('user_id')
        if user_id in self.user_baselines:
            baseline = self.user_baselines[user_id]
            features.extend([
                baseline.get('avg_session_events', 5),
                baseline.get('avg_purchase_amount', 25.0),
                baseline.get('sessions_count', 1)
            ])
        else:
            features.extend([5, 25.0, 1])  # Default values
        
        # Sequence features (if available)
        causality_chain = event.get('causality_chain', [])
        features.extend([
            len(causality_chain),
            1 if causality_chain else 0  # Has parent events
        ])
        
        return np.array(features).reshape(1, -1)
    
    def update_user_baseline(self, event: Dict[str, Any]):
        """Update user behavioral baseline"""
        user_id = event.get('user_id')
        if not user_id:
            return
        
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {
                'events': [],
                'sessions': set(),
                'purchases': [],
                'last_seen': time.time()
            }
        
        baseline = self.user_baselines[user_id]
        baseline['events'].append(event)
        baseline['last_seen'] = time.time()
        
        session_id = event.get('session_id')
        if session_id:
            baseline['sessions'].add(session_id)
        
        if event.get('event_type') == 'purchase':
            amount = event.get('properties', {}).get('amount', 0)
            if amount:
                baseline['purchases'].append(float(amount))
        
        # Calculate running averages
        baseline['avg_session_events'] = len(baseline['events']) / max(1, len(baseline['sessions']))
        baseline['avg_purchase_amount'] = np.mean(baseline['purchases']) if baseline['purchases'] else 25.0
        baseline['sessions_count'] = len(baseline['sessions'])
        
        # Keep only recent data (last 7 days)
        cutoff_time = time.time() - 7 * 24 * 3600
        baseline['events'] = [
            e for e in baseline['events'] 
            if e.get('timestamp', 0) / 1000 > cutoff_time
        ]
    
    def detect_behavioral_anomalies(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Detect behavioral anomalies using rule-based approach"""
        anomalies = {}
        
        user_id = event.get('user_id')
        event_type = event.get('event_type')
        properties = event.get('properties', {})
        
        # Rapid fire events (potential bot behavior)
        if user_id in self.user_baselines:
            recent_events = [
                e for e in self.user_baselines[user_id]['events']
                if e.get('timestamp', 0) / 1000 > time.time() - 60  # Last minute
            ]
            
            if len(recent_events) > 20:  # More than 20 events per minute
                anomalies['rapid_fire'] = {
                    'score': min(1.0, len(recent_events) / 50),
                    'events_per_minute': len(recent_events)
                }
        
        # Unusual purchase amounts
        if event_type == 'purchase':
            amount = properties.get('amount', 0)
            if amount:
                amount = float(amount)
                
                # Compare to user baseline
                if user_id in self.user_baselines:
                    user_avg = self.user_baselines[user_id].get('avg_purchase_amount', 50.0)
                    if amount > user_avg * 5:  # 5x higher than usual
                        anomalies['unusual_purchase'] = {
                            'score': min(1.0, amount / (user_avg * 10)),
                            'amount': amount,
                            'user_average': user_avg
                        }
                
                # Compare to global baseline
                if amount > self.global_baseline['avg_purchase_amount'] * 10:
                    anomalies['high_value_purchase'] = {
                        'score': min(1.0, amount / 1000),
                        'amount': amount
                    }
        
        # Unusual time patterns
        timestamp = event.get('timestamp', time.time() * 1000) / 1000
        hour = pd.to_datetime(timestamp, unit='s').hour
        
        if hour < 6 or hour > 23:  # Late night activity
            anomalies['unusual_time'] = {
                'score': 0.3,
                'hour': hour
            }
        
        return anomalies
    
    def train_model(self):
        """Train/retrain the ML model"""
        if len(self.feature_buffer) < 100:
            return
        
        logger.info(f"Training anomaly detection model with {len(self.feature_buffer)} samples")
        
        try:
            # Prepare training data
            X = np.array(list(self.feature_buffer))
            
            # Handle NaN values
            X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.isolation_forest.fit(X_scaled)
            
            # Estimate model accuracy (simplified)
            predictions = self.isolation_forest.predict(X_scaled)
            outlier_ratio = np.sum(predictions == -1) / len(predictions)
            
            # Update model metrics
            model_accuracy.set(1.0 - abs(outlier_ratio - 0.1))  # Target 10% outliers
            
            self.is_trained = True
            self.model_version += 1
            
            logger.info(f"Model trained successfully. Version: {self.model_version}, Outlier ratio: {outlier_ratio:.3f}")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    def get_ml_anomaly_score(self, event: Dict[str, Any]) -> float:
        """Get ML-based anomaly score"""
        if not self.is_trained:
            return 0.0
        
        try:
            features = self.extract_features(event)
            features = np.nan_to_num(features, nan=0.0, posinf=1e6, neginf=-1e6)
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score from Isolation Forest
            score = self.isolation_forest.decision_function(features_scaled)[0]
            
            # Convert to 0-1 scale (higher = more anomalous)
            normalized_score = max(0, min(1, (0.5 - score) / 1.0))
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"ML inference error: {e}")
            return 0.0
    
    def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive event analysis"""
        with tracer.start_as_current_span("analyze_event") as span:
            start_time = time.time()
            
            # Update user baselines
            self.update_user_baseline(event)
            
            # Extract features and add to buffer
            features = self.extract_features(event)
            self.feature_buffer.append(features[0])
            
            # Get ML anomaly score
            ml_score = self.get_ml_anomaly_score(event)
            
            # Get behavioral anomalies
            behavioral_anomalies = self.detect_behavioral_anomalies(event)
            
            # Combine scores
            max_behavioral_score = max(
                [a.get('score', 0) for a in behavioral_anomalies.values()],
                default=0
            )
            
            combined_score = max(ml_score, max_behavioral_score)
            
            # Create analysis result
            result = {
                'event_id': event.get('event_id'),
                'user_id': event.get('user_id'),
                'timestamp': event.get('timestamp'),
                'ml_anomaly_score': ml_score,
                'behavioral_anomalies': behavioral_anomalies,
                'combined_anomaly_score': combined_score,
                'is_anomaly': combined_score > 0.7,
                'model_version': self.model_version,
                'analysis_time': time.time() - start_time
            }
            
            # Update metrics
            events_analyzed.inc()
            ml_inference_latency.observe(time.time() - start_time)
            
            if result['is_anomaly']:
                anomaly_type = 'ml' if ml_score > max_behavioral_score else 'behavioral'
                anomalies_detected.labels(anomaly_type=anomaly_type).inc()
            
            # Store anomaly for pattern analysis
            if combined_score > 0.5:
                self.anomaly_buffer.append(result)
            
            span.set_attribute("anomaly_score", combined_score)
            span.set_attribute("is_anomaly", result['is_anomaly'])
            
            return result

class MLDetectorService:
    """Main ML detector service"""
    
    def __init__(self):
        self.cluster_nodes = [
            {"host": host.split(":")[0], "port": int(host.split(":")[1])}
            for host in REDIS_CLUSTER.split(",")
        ]
        self.redis_cluster = None
        self.detector = AdvancedAnomalyDetector()
        
    async def initialize(self):
        """Initialize Redis connection and consumer group"""
        self.redis_cluster = RedisCluster(
            startup_nodes=self.cluster_nodes,
            decode_responses=True,
            skip_full_coverage_check=True
        )
        
        # Create consumer group for processed events
        try:
            await self.redis_cluster.xgroup_create(
                "processed_events", CONSUMER_GROUP, id='0', mkstream=True
            )
        except Exception:
            pass  # Group already exists
    
    async def process_events(self):
        """Main event processing loop"""
        logger.info(f"ML Detector starting: {CONSUMER_NAME}")
        
        while True:
            try:
                # Read processed events
                streams = await self.redis_cluster.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {"processed_events": '>'},
                    count=50,
                    block=5000
                )
                
                if not streams:
                    # Retrain model periodically
                    if len(self.detector.feature_buffer) >= 100:
                        self.detector.train_model()
                    continue
                
                # Process batch of events
                for stream_name, messages in streams:
                    for msg_id, fields in messages:
                        try:
                            # Parse processed event
                            processed_event_data = orjson.loads(fields['data'])
                            original_event = processed_event_data.get('original_event', {})
                            
                            # Analyze for anomalies
                            analysis = self.detector.analyze_event(original_event)
                            
                            # Store analysis results
                            if analysis['is_anomaly']:
                                await self.store_anomaly(analysis)
                            
                            # Acknowledge message
                            await self.redis_cluster.xack(stream_name, CONSUMER_GROUP, msg_id)
                            
                        except Exception as e:
                            logger.error(f"Error processing event {msg_id}: {e}")
                
            except Exception as e:
                logger.error(f"ML detector loop error: {e}")
                await asyncio.sleep(5)
    
    async def store_anomaly(self, analysis: Dict[str, Any]):
        """Store detected anomaly for alerting"""
        try:
            # Store in Redis for real-time access
            anomaly_key = f"anomaly:{analysis['event_id']}"
            await self.redis_cluster.hset(anomaly_key, mapping={
                'data': orjson.dumps(analysis),
                'timestamp': analysis['timestamp'],
                'score': analysis['combined_anomaly_score']
            })
            
            # Set expiration (keep for 24 hours)
            await self.redis_cluster.expire(anomaly_key, 86400)
            
            # Add to anomaly stream for alerting
            await self.redis_cluster.xadd("anomaly_alerts", {
                'anomaly_id': analysis['event_id'],
                'score': analysis['combined_anomaly_score'],
                'type': 'ml_detected',
                'data': orjson.dumps(analysis)
            })
            
            logger.warning(f"Anomaly detected: {analysis['event_id']} (score: {analysis['combined_anomaly_score']:.3f})")
            
        except Exception as e:
            logger.error(f"Error storing anomaly: {e}")
    
    async def run(self):
        """Run the ML detector service"""
        await self.initialize()
        
        # Start metrics server
        start_http_server(8000)
        
        # Start processing
        await self.process_events()

if __name__ == "__main__":
    detector_service = MLDetectorService()
    asyncio.run(detector_service.run())