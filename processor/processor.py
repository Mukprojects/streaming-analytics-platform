import os
import time
import threading
import json
from collections import defaultdict
from flask import Flask, Response
import redis
from prometheus_client import start_http_server, Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_KEY = os.getenv("STREAM_KEY", "events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "event_group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "proc-1")
AGG_KEY = os.getenv("AGG_KEY", "aggregates")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Prometheus metrics
events_processed = Counter('events_processed_total', 'Total events processed')
processing_latency = Histogram('processing_latency_seconds', 'Processing latency in seconds')
event_type_count = Counter('event_type_count', 'Count per event type', ['event_type'])
stream_lag = Gauge('stream_lag_seconds', 'Lag between event timestamp and processing time')
last_processed_id = Gauge('last_processed_id', 'Last processed stream id (as float approximation)')
consumer_group_pending = Gauge('consumer_group_pending', 'Number of pending messages in consumer group')

# Flask app to expose /metrics and /health
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    return {"status": "ok", "consumer": CONSUMER_NAME}

def ensure_group():
    try:
        r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id='0', mkstream=True)
        print(f"Consumer group '{CONSUMER_GROUP}' created")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{CONSUMER_GROUP}' already exists")
        else:
            print(f"Group creation error: {e}")

def update_aggregates(msg):
    """Update aggregates in Redis atomically"""
    event_type = msg.get("event_type")
    event_ts = float(msg.get("ts", 0)) / 1000.0
    current_ts = time.time()
    
    # Calculate and record lag
    lag = current_ts - event_ts
    stream_lag.set(lag)
    
    # Update counters
    if event_type:
        r.hincrby(AGG_KEY, f"type:{event_type}:count", 1)
        event_type_count.labels(event_type).inc()
    
    # Update session tracking
    session_id = msg.get("session_id")
    if session_id:
        r.hincrby(AGG_KEY, f"session:{session_id}:events", 1)
    
    # Update product tracking
    product = msg.get("product")
    if product:
        r.hincrby(AGG_KEY, f"product:{product}:count", 1)
    
    # Overall metrics
    r.hincrby(AGG_KEY, "total_count", 1)
    r.hset(AGG_KEY, "last_updated", int(current_ts))

def process_message(msg_id, msg):
    """Process a single message"""
    start_time = time.time()
    
    try:
        update_aggregates(msg)
        
        # Update metrics
        events_processed.inc()
        processing_latency.observe(time.time() - start_time)
        
        # Update last processed ID for monitoring
        stream_id_parts = msg_id.split('-')
        if len(stream_id_parts) >= 1:
            last_processed_id.set(float(stream_id_parts[0]))
        
        return True
    except Exception as e:
        print(f"Error processing message {msg_id}: {e}")
        return False

def process_loop():
    ensure_group()
    print(f"Starting processor loop: {CONSUMER_NAME} in group {CONSUMER_GROUP}")
    
    while True:
        try:
            # Read new messages
            resp = r.xreadgroup(
                CONSUMER_GROUP, 
                CONSUMER_NAME, 
                {STREAM_KEY: '>'}, 
                count=100, 
                block=5000
            )
            
            if not resp:
                # Check for pending messages (recovery)
                pending_info = r.xpending(STREAM_KEY, CONSUMER_GROUP)
                if pending_info and pending_info['pending'] > 0:
                    consumer_group_pending.set(pending_info['pending'])
                    
                    # Claim and reprocess old pending messages
                    pending = r.xpending_range(
                        STREAM_KEY, 
                        CONSUMER_GROUP, 
                        '-', '+', 
                        count=10
                    )
                    
                    for p in pending:
                        msg_id = p['message_id']
                        idle_time = p['time_since_delivered']
                        
                        # Claim messages idle for more than 30 seconds
                        if idle_time > 30000:
                            try:
                                claimed = r.xclaim(
                                    STREAM_KEY, 
                                    CONSUMER_GROUP, 
                                    CONSUMER_NAME,
                                    min_idle_time=30000,
                                    message_ids=[msg_id]
                                )
                                
                                for c_msg_id, c_data in claimed:
                                    if process_message(c_msg_id, c_data):
                                        r.xack(STREAM_KEY, CONSUMER_GROUP, c_msg_id)
                                        
                            except Exception as e:
                                print(f"Error claiming message {msg_id}: {e}")
                else:
                    consumer_group_pending.set(0)
                continue
            
            # Process new messages
            for stream_name, messages in resp:
                for msg_id, data in messages:
                    if process_message(msg_id, data):
                        r.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                        
        except Exception as e:
            print(f"Error in processing loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    # Start Prometheus metrics endpoint
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=METRICS_PORT), 
        daemon=True
    ).start()
    
    print(f"Starting processor; metrics on :{METRICS_PORT}/metrics")
    process_loop()