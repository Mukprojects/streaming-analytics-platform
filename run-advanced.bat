@echo off
echo ========================================
echo   NEXT-GENERATION STREAMING PIPELINE
echo ========================================
echo.
echo This advanced system includes:
echo - Redis Cluster (3 nodes)
echo - Multi-stage processing pipeline
echo - ML-powered anomaly detection
echo - GraphQL API with real-time subscriptions
echo - Distributed tracing with Jaeger
echo - Chaos engineering with automated failure injection
echo - Advanced monitoring and alerting
echo.

echo Starting advanced pipeline...
docker-compose -f docker-compose.advanced.yml up --build -d

echo.
echo Waiting for services to initialize (60 seconds)...
timeout /t 60 /nobreak > nul

echo.
echo Service Status:
docker-compose -f docker-compose.advanced.yml ps

echo.
echo ========================================
echo   ACCESS POINTS
echo ========================================
echo - Grafana Dashboard: http://localhost:3000 (admin/admin)
echo - Prometheus: http://localhost:9090
echo - Jaeger Tracing: http://localhost:16686
echo - GraphQL Playground: http://localhost:8080/graphql
echo - WebSocket Streaming: ws://localhost:8080/ws
echo - Advanced API: http://localhost:8080/v2/aggregates
echo.

echo ========================================
echo   ADVANCED TESTING
echo ========================================
echo - Run Advanced Benchmark: python advanced-benchmark.py
echo - Monitor Chaos Experiments: docker-compose -f docker-compose.advanced.yml logs chaos-monkey
echo - View Distributed Traces: Open Jaeger UI
echo - Test GraphQL: Open GraphQL Playground
echo.

echo System is ready for demonstration!
echo This showcases Google-level distributed systems engineering.
echo.
pause