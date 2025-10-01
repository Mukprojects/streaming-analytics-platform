import os
import time
import json
import random
import redis
import orjson
from time import perf_counter

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
STREAM_KEY = os.getenv("STREAM_KEY", "events")
RATE = int(os.getenv("RATE", "100"))  # events per second

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=False)

EVENT_TYPES = ["click", "view", "purchase", "signup", "logout", "search"]
PRODUCTS = ["laptop", "phone", "tablet", "headphones", "camera"]

def make_event(i):
    ts = int(time.time() * 1000)
    ev = {
        "event_id": str(i),
        "user_id": str(random.randint(1, 10000)),
        "event_type": random.choice(EVENT_TYPES),
        "product": random.choice(PRODUCTS) if random.random() > 0.3 else None,
        "value": str(round(random.random() * 100, 2)),
        "session_id": str(random.randint(1, 1000)),
        "ts": str(ts)
    }
    return {k: v for k, v in ev.items() if v is not None}

def run():
    i = 0
    interval = 1.0 / RATE
    print(f"Producer starting -> {REDIS_HOST}/{STREAM_KEY} at {RATE} ev/s")
    
    while True:
        start = perf_counter()
        ev = make_event(i)
        
        try:
            # xadd accepts string values
            r.xadd(STREAM_KEY, ev)
            i += 1
            
            if i % 1000 == 0:
                print(f"Produced {i} events")
                
        except Exception as e:
            print(f"Error producing event: {e}")
            time.sleep(1)
            continue
        
        # Rate limiting
        elapsed = perf_counter() - start
        to_sleep = interval - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)

if __name__ == "__main__":
    run()