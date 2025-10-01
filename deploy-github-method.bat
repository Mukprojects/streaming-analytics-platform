@echo off
echo ========================================
echo 🚀 GITHUB + RAILWAY WEB DEPLOYMENT
echo ========================================
echo.
echo This method is more reliable than CLI installation!
echo.

echo Step 1: Create GitHub Repository
echo ================================
echo.
echo 1. Go to https://github.com/new
echo 2. Repository name: streaming-analytics-platform
echo 3. Make it public
echo 4. Don't initialize with README (we have files)
echo 5. Click "Create repository"
echo.

echo Step 2: Push Your Code to GitHub
echo =================================
echo.
echo Run these commands in order:
echo.
echo git init
echo git add .
echo git commit -m "Add streaming analytics platform"
echo git branch -M main
echo git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
echo git push -u origin main
echo.
echo (Replace YOURUSERNAME with your GitHub username)
echo.

echo Step 3: Deploy via Railway Web Interface
echo =========================================
echo.
echo 1. Go to https://railway.app/
echo 2. Click "Login" and sign in with GitHub
echo 3. Click "New Project"
echo 4. Select "Deploy from GitHub repo"
echo 5. Choose your streaming-analytics-platform repository
echo 6. Railway will automatically deploy!
echo.

echo Step 4: Configure Environment Variables
echo ========================================
echo.
echo In Railway dashboard, go to Variables tab and add:
echo   REDIS_HOST = redis
echo   RATE = 100
echo   PORT = 8080
echo   STREAM_KEY = events
echo   CONSUMER_GROUP = event_group
echo   AGG_KEY = aggregates
echo   METRICS_PORT = 8000
echo.

echo ✅ Your system will be live at the Railway URL!
echo.
echo 🎯 Want me to prepare the files for GitHub?
set /p choice="Prepare GitHub files? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo Preparing files for GitHub deployment...
    
    REM Copy the basic docker-compose for Railway
    copy deployment\railway-deploy.yml docker-compose.yml
    
    REM Copy the impressive README
    copy portfolio-README.md README.md
    
    echo.
    echo ✅ Files prepared! Now run:
    echo.
    echo git init
    echo git add .
    echo git commit -m "Add streaming analytics platform"
    echo git branch -M main
    echo git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
    echo git push -u origin main
    echo.
    echo Then deploy via Railway web interface!
)

echo.
pause