@echo off
echo ========================================
echo 🚀 RENDER.COM DEPLOYMENT (FREE TIER)
echo ========================================
echo.
echo Render.com is easier and has better free tier!
echo.

echo Step 1: Prepare Files for Render
echo =================================
echo.
copy deployment\render-deploy.yml docker-compose.yml
copy portfolio-README.md README.md
echo ✅ Files prepared for Render deployment
echo.

echo Step 2: Create GitHub Repository
echo ================================
echo.
echo 1. Go to https://github.com/new
echo 2. Repository name: streaming-analytics-platform
echo 3. Make it public
echo 4. Click "Create repository"
echo.

echo Step 3: Push to GitHub
echo ======================
echo.
echo Run these commands:
echo.
echo git init
echo git add .
echo git commit -m "Add streaming analytics platform"
echo git branch -M main
echo git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
echo git push -u origin main
echo.

echo Step 4: Deploy on Render
echo =========================
echo.
echo 1. Go to https://render.com/
echo 2. Sign up/login with GitHub
echo 3. Click "New +" then "Web Service"
echo 4. Connect your GitHub repository
echo 5. Choose "streaming-analytics-platform"
echo 6. Render will auto-detect Docker and deploy!
echo.

echo Step 5: Add Redis Database
echo ===========================
echo.
echo 1. In Render dashboard, click "New +" then "Redis"
echo 2. Choose free plan
echo 3. Note the Redis URL
echo 4. In your web service, add environment variable:
echo    REDIS_HOST = [your-redis-url]
echo.

echo ✅ Your system will be live at render URL!
echo.
echo 🎯 Render Advantages:
echo   - Free Redis database included
echo   - Automatic HTTPS
echo   - Easy scaling
echo   - Better free tier than Railway
echo.

set /p choice="Prepare files for Render deployment? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo ✅ Files already prepared!
    echo.
    echo Next steps:
    echo 1. Create GitHub repo
    echo 2. Push code with git commands above
    echo 3. Deploy on Render.com
    echo.
    echo Your streaming platform will be live!
)

echo.
pause