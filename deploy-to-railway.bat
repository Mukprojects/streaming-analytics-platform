@echo off
echo ========================================
echo 🚀 DEPLOYING STREAMING PIPELINE TO RAILWAY
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js not found. Please install Node.js first:
    echo    https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Railway CLI is installed
where railway >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 📦 Installing Railway CLI...
    npm install -g @railway/cli
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install Railway CLI
        pause
        exit /b 1
    )
)

REM Check Railway authentication
echo 🔐 Checking Railway authentication...
railway whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Please login to Railway (this will open your browser):
    railway login
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Railway login failed
        pause
        exit /b 1
    )
)

REM Create new Railway project
echo 📦 Creating new Railway project...
railway new
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create Railway project
    pause
    exit /b 1
)

REM Set up environment variables
echo ⚙️ Setting up environment variables...
railway variables set REDIS_HOST=redis
railway variables set STREAM_KEY=events
railway variables set RATE=100
railway variables set CONSUMER_GROUP=event_group
railway variables set AGG_KEY=aggregates
railway variables set METRICS_PORT=8000
railway variables set PORT=8080

REM Copy deployment configuration
echo 📋 Preparing deployment configuration...
copy deployment\railway-deploy.yml docker-compose.yml
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to copy deployment config
    pause
    exit /b 1
)

REM Deploy the application
echo 🚀 Deploying application...
railway up
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Deployment failed
    pause
    exit /b 1
)

REM Get deployment info
echo 🔗 Getting deployment information...
railway status

echo.
echo ✅ DEPLOYMENT COMPLETE!
echo ========================
echo.
echo 🎯 Your streaming pipeline is now live!
echo.
echo 📊 Access your system:
echo   - Main Dashboard: Check Railway dashboard for URL
echo   - Grafana: [your-url]:3000 (admin/demo123)
echo   - Prometheus: [your-url]:9090
echo   - API: [your-url]:8080/aggregates
echo.
echo 💡 Next Steps:
echo   1. Get your Railway URL from the dashboard
echo   2. Update portfolio-landing.html with your URL
echo   3. Create GitHub repository
echo   4. Add live demo links to your resume
echo.
echo 🚀 Your portfolio just got a major upgrade!
echo.
pause