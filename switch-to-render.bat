@echo off
echo ========================================
echo 🎯 SWITCH TO RENDER.COM (RECOMMENDED)
echo ========================================
echo.

echo Railway is being difficult with Docker Compose.
echo Render.com handles this much better!
echo.

echo Preparing files for Render deployment...
echo.

REM Copy the Render-optimized docker-compose
copy deployment\render-deploy.yml docker-compose.yml
echo ✅ Render-optimized docker-compose.yml

REM Create render.yaml for better detection
(
echo services:
echo   - type: web
echo     name: streaming-platform
echo     env: docker
echo     dockerfilePath: ./Dockerfile
echo     plan: free
echo     healthCheckPath: /health
echo     envVars:
echo       - key: REDIS_HOST
echo         value: redis
echo       - key: RATE  
echo         value: 100
echo       - key: PORT
echo         value: 8080
echo.
echo   - type: redis
echo     name: redis
echo     plan: free
echo     maxmemoryPolicy: allkeys-lru
) > render.yaml
echo ✅ render.yaml configuration

echo.
echo ========================================
echo 🚀 DEPLOY ON RENDER.COM
echo ========================================
echo.

echo 1. COMMIT CHANGES:
echo    git add .
echo    git commit -m "Switch to Render deployment"
echo    git push
echo.

echo 2. DEPLOY ON RENDER:
echo    - Go to https://render.com/
echo    - Sign up/login with GitHub
echo    - Click "New +" then "Web Service"
echo    - Connect your GitHub repository
echo    - Render will auto-detect and deploy!
echo.

echo 3. ADD REDIS DATABASE:
echo    - In Render dashboard, click "New +" then "Redis"
echo    - Choose free plan
echo    - Connect to your web service
echo.

echo ✅ RENDER ADVANTAGES:
echo   - Better Docker Compose support
echo   - Free Redis database included
echo   - Easier configuration
echo   - More reliable deployments
echo   - Better free tier limits
echo.

set /p choice="Commit files for Render deployment? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo Committing Render configuration...
    git add .
    git commit -m "Add Render deployment configuration"
    
    echo.
    echo ✅ Ready for Render! Now:
    echo 1. Push to GitHub: git push
    echo 2. Deploy on https://render.com/
    echo.
    
    set /p open="Open Render.com now? (y/n): "
    if /i "%open%"=="y" (
        start https://render.com/
    )
)

echo.
echo 🎯 Your streaming platform will be live on Render!
echo.
pause