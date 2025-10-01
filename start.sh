#!/bin/bash

# Railway start script for streaming platform
echo "🚀 Starting Streaming Analytics Platform..."

# Start the API service (main service for Railway)
cd api
uvicorn api:app --host 0.0.0.0 --port $PORT