@echo off
echo Running Performance Benchmark...
echo.

cd bench
python benchmark.py

echo.
echo Benchmark complete! Check benchmark_results.json for detailed results.
pause