@echo off
echo Testing Failure Recovery...
echo.

echo Current event count before failure:
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8080/aggregates/summary' | Select-Object -ExpandProperty Content"

echo.
echo Stopping processor to simulate crash...
docker compose stop processor

echo.
echo Waiting 10 seconds (simulating downtime)...
timeout /t 10 /nobreak > nul

echo.
echo Restarting processor...
docker compose start processor

echo.
echo Waiting 5 seconds for recovery...
timeout /t 5 /nobreak > nul

echo.
echo Event count after recovery:
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8080/aggregates/summary' | Select-Object -ExpandProperty Content"

echo.
echo Recovery test complete! Events should continue processing with no data loss.
pause