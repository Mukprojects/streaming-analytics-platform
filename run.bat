@echo off
echo Starting Distributed Streaming Pipeline...
echo.

echo Building and starting all services...
docker-compose up --build -d

echo.
echo Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak > nul

echo.
echo Service Status:
docker-compose ps

echo.
echo Access Points:
echo - Grafana Dashboard: http://localhost:3000 (admin/admin)
echo - Prometheus: http://localhost:9090  
echo - API Aggregates: http://localhost:8080/aggregates
echo - API Health: http://localhost:8080/health

echo.
echo To monitor logs: docker-compose logs -f producer processor
echo To run benchmark: python bench/benchmark.py
echo To test failure recovery: fail/fail_consumer.sh (use Git Bash on Windows)
echo.
echo Press any key to continue...
pause > nul