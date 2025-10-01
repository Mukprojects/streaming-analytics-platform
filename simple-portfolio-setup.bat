@echo off
echo ========================================
echo 🎯 SIMPLE PORTFOLIO SETUP
echo ========================================
echo.
echo Let's get your streaming platform online the easy way!
echo.

echo Preparing your files for deployment...
echo.

REM Copy the best deployment config
copy deployment\render-deploy.yml docker-compose.yml
echo ✅ Deployment config ready

REM Copy the impressive README
copy portfolio-README.md README.md
echo ✅ Portfolio README ready

REM Create a simple deployment guide
echo Creating deployment guide...
(
echo # 🚀 Quick Deployment Guide
echo.
echo ## Option 1: Render.com ^(Recommended^)
echo 1. Push this code to GitHub
echo 2. Go to https://render.com/
echo 3. Connect GitHub and deploy
echo 4. Add Redis database ^(free^)
echo.
echo ## Option 2: Railway.app
echo 1. Push this code to GitHub  
echo 2. Go to https://railway.app/
echo 3. Deploy from GitHub
echo.
echo ## Your URLs will be:
echo - Main app: https://your-app.render.com
echo - Grafana: https://your-app.render.com:3000
echo - API: https://your-app.render.com:8080/aggregates
echo.
echo ## Add to your resume:
echo "Real-time Streaming Analytics Platform - [your-url]"
echo "Production system processing 500+ events/sec with monitoring"
) > DEPLOYMENT.md
echo ✅ Deployment guide created

echo.
echo ========================================
echo 🎯 YOUR FILES ARE READY!
echo ========================================
echo.
echo What's been prepared:
echo   ✅ docker-compose.yml - Deployment configuration
echo   ✅ README.md - Impressive project description
echo   ✅ DEPLOYMENT.md - Simple deployment steps
echo.
echo 🚀 NEXT STEPS:
echo.
echo 1. CREATE GITHUB REPOSITORY:
echo    - Go to https://github.com/new
echo    - Name: streaming-analytics-platform
echo    - Make it public
echo.
echo 2. PUSH YOUR CODE:
echo    git init
echo    git add .
echo    git commit -m "Add streaming analytics platform"
echo    git branch -M main
echo    git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
echo    git push -u origin main
echo.
echo 3. DEPLOY ONLINE:
echo    - Go to https://render.com/ ^(easiest^)
echo    - Or https://railway.app/
echo    - Connect GitHub and deploy
echo.
echo 4. UPDATE YOUR PORTFOLIO:
echo    - Add live demo link to resume
echo    - Post on LinkedIn about your system
echo    - Include in portfolio website
echo.
echo ✅ You'll have a live streaming platform for your portfolio!
echo.

set /p choice="Open deployment guide? (y/n): "
if /i "%choice%"=="y" (
    start DEPLOYMENT.md
)

echo.
echo 🎯 Your streaming platform is ready for the world!
echo    Just push to GitHub and deploy online.
echo.
pause