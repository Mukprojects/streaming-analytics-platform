import os
import time
from typing import Dict, Any
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
AGG_KEY = os.getenv("AGG_KEY", "aggregates")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
app = FastAPI(title="Streaming Pipeline API", version="1.0.0")

# API metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
api_latency = Histogram('api_request_duration_seconds', 'API request latency')

@app.middleware("http")
async def add_metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Record metrics
    api_requests.labels(
        endpoint=request.url.path, 
        method=request.method
    ).inc()
    api_latency.observe(time.time() - start_time)
    
    return response

@app.get("/")
def root():
    return {
        "service": "streaming-pipeline-api",
        "version": "1.0.0",
        "endpoints": {
            "aggregates": "/aggregates",
            "metrics": "/metrics",
            "health": "/health"
        }
    }

@app.get("/health")
def health():
    try:
        # Test Redis connection
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {e}")

@app.get("/aggregates")
def get_aggregates() -> Dict[str, Any]:
    try:
        data = r.hgetall(AGG_KEY)
        
        if not data:
            return {"aggregates": {}, "message": "No data available yet"}
        
        # Parse and organize data
        parsed = {}
        event_types = {}
        sessions = {}
        products = {}
        
        for k, v in data.items():
            try:
                # Convert to appropriate numeric type
                numeric_value = float(v) if '.' in v else int(v)
                
                if k.startswith("type:"):
                    # Event type aggregates
                    parts = k.split(":")
                    if len(parts) >= 3:
                        event_type = parts[1]
                        metric = parts[2]
                        if event_type not in event_types:
                            event_types[event_type] = {}
                        event_types[event_type][metric] = numeric_value
                elif k.startswith("session:"):
                    # Session aggregates
                    parts = k.split(":")
                    if len(parts) >= 3:
                        session_id = parts[1]
                        metric = parts[2]
                        if session_id not in sessions:
                            sessions[session_id] = {}
                        sessions[session_id][metric] = numeric_value
                elif k.startswith("product:"):
                    # Product aggregates
                    parts = k.split(":")
                    if len(parts) >= 3:
                        product = parts[1]
                        metric = parts[2]
                        if product not in products:
                            products[product] = {}
                        products[product][metric] = numeric_value
                else:
                    # General metrics
                    parsed[k] = numeric_value
                    
            except (ValueError, TypeError):
                parsed[k] = v
        
        # Calculate derived metrics
        total_count = parsed.get("total_count", 0)
        last_updated = parsed.get("last_updated", 0)
        
        result = {
            "aggregates": {
                "overview": {
                    "total_events": total_count,
                    "last_updated": last_updated,
                    "last_updated_human": time.ctime(last_updated) if last_updated else None
                },
                "event_types": event_types,
                "top_products": dict(sorted(
                    products.items(), 
                    key=lambda x: x[1].get('count', 0), 
                    reverse=True
                )[:10]),
                "active_sessions": len(sessions),
                "raw": parsed
            },
            "timestamp": time.time()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching aggregates: {e}")

@app.get("/aggregates/summary")
def get_summary():
    """Get a quick summary of key metrics"""
    try:
        total = r.hget(AGG_KEY, "total_count") or "0"
        last_updated = r.hget(AGG_KEY, "last_updated") or "0"
        
        # Get top event types
        data = r.hgetall(AGG_KEY)
        event_types = {}
        for k, v in data.items():
            if k.startswith("type:") and k.endswith(":count"):
                event_type = k.split(":")[1]
                event_types[event_type] = int(v)
        
        return {
            "total_events": int(total),
            "last_updated": int(last_updated),
            "top_event_types": dict(sorted(
                event_types.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {e}")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)