@echo off
echo ========================================
echo 🚀 SIMPLE RAILWAY DEPLOYMENT GUIDE
echo ========================================
echo.

echo This will guide you through deploying your streaming pipeline to Railway.app
echo.

echo Step 1: Install Node.js (if not installed)
echo   Download from: https://nodejs.org/
echo   Then restart this script
echo.

echo Step 2: Install Railway CLI
echo   Run: npm install -g @railway/cli
echo.

echo Step 3: Login to Railway
echo   Run: railway login
echo.

echo Step 4: Create new project
echo   Run: railway new
echo.

echo Step 5: Set environment variables
echo   railway variables set REDIS_HOST=redis
echo   railway variables set RATE=100
echo   railway variables set PORT=8080
echo.

echo Step 6: Copy deployment config
echo   copy deployment\railway-deploy.yml docker-compose.yml
echo.

echo Step 7: Deploy
echo   railway up
echo.

echo ✅ Your system will be live at the Railway URL!
echo.

echo 🎯 Want to run these commands automatically?
echo.
set /p choice="Run automatic deployment? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo Running automatic deployment...
    echo.
    
    REM Install Railway CLI
    npm install -g @railway/cli
    
    REM Login
    railway login
    
    REM Create project
    railway new
    
    REM Set variables
    railway variables set REDIS_HOST=redis
    railway variables set RATE=100
    railway variables set PORT=8080
    
    REM Copy config
    copy deployment\railway-deploy.yml docker-compose.yml
    
    REM Deploy
    railway up
    
    echo.
    echo ✅ Deployment complete! Check Railway dashboard for your URL.
)

pause