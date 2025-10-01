#!/usr/bin/env python3
"""
Local setup script to run the pipeline components without Docker.
Requires Redis to be installed locally.
"""
import subprocess
import sys
import time
import threading
import os

def install_requirements():
    """Install Python requirements for all services"""
    requirements = [
        "redis", "orjson", "flask", "fastapi", "uvicorn", 
        "prometheus-client", "requests"
    ]
    
    print("Installing Python requirements...")
    for req in requirements:
        subprocess.run([sys.executable, "-m", "pip", "install", req])

def start_redis():
    """Instructions for starting Redis locally"""
    print("""
    To run locally, you need Redis installed:
    
    Windows (using Chocolatey):
    choco install redis-64
    redis-server
    
    Or download from: https://github.com/microsoftarchive/redis/releases
    
    Linux/Mac:
    sudo apt-get install redis-server  # Ubuntu
    brew install redis                 # Mac
    redis-server
    """)

def run_producer():
    """Run the producer service"""
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["RATE"] = "100"
    
    import sys
    sys.path.append("producer")
    from producer import run
    run()

def run_processor():
    """Run the processor service"""
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["METRICS_PORT"] = "8000"
    
    import sys
    sys.path.append("processor")
    from processor import process_loop, app
    
    # Start metrics server
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8000), 
        daemon=True
    ).start()
    
    process_loop()

def run_api():
    """Run the API service"""
    os.environ["REDIS_HOST"] = "localhost"
    
    import sys
    sys.path.append("api")
    
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "api:app", "--host", "0.0.0.0", "--port", "8080"
    ])

if __name__ == "__main__":
    print("Local Pipeline Setup")
    print("=" * 50)
    
    choice = input("""
    Choose an option:
    1. Install requirements only
    2. Start producer (requires Redis running)
    3. Start processor (requires Redis running)  
    4. Start API (requires Redis running)
    5. Show Redis installation instructions
    
    Enter choice (1-5): """)
    
    if choice == "1":
        install_requirements()
    elif choice == "2":
        run_producer()
    elif choice == "3":
        run_processor()
    elif choice == "4":
        run_api()
    elif choice == "5":
        start_redis()
    else:
        print("Invalid choice")