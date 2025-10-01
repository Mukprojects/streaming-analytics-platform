@echo off
echo ========================================
echo 🚀 EASY WEB DEPLOYMENT (NO CLI NEEDED!)
echo ========================================
echo.
echo The CLI is giving us trouble, so let's use the web interface instead.
echo This is actually EASIER and more reliable!
echo.

echo Preparing your files for web deployment...
echo.

REM Copy the deployment config
copy deployment\render-deploy.yml docker-compose.yml
echo ✅ Docker config ready

REM Copy the impressive README
copy portfolio-README.md README.md
echo ✅ README ready

REM Create .gitignore
(
echo node_modules/
echo *.log
echo .env
echo __pycache__/
echo *.pyc
echo .DS_Store
) > .gitignore
echo ✅ .gitignore created

echo.
echo ========================================
echo 🎯 YOUR FILES ARE READY FOR DEPLOYMENT!
echo ========================================
echo.

echo 📋 STEP 1: CREATE GITHUB REPOSITORY
echo ====================================
echo.
echo 1. Go to: https://github.com/new
echo 2. Repository name: streaming-analytics-platform
echo 3. Make it PUBLIC
echo 4. Don't initialize with README
echo 5. Click "Create repository"
echo.

echo 📋 STEP 2: PUSH YOUR CODE TO GITHUB
echo ===================================
echo.
echo Copy and run these commands ONE BY ONE:
echo.
echo git init
echo git add .
echo git commit -m "Add streaming analytics platform"
echo git branch -M main
echo git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
echo git push -u origin main
echo.
echo (Replace YOURUSERNAME with your actual GitHub username)
echo.

echo 📋 STEP 3: DEPLOY ON RENDER.COM (RECOMMENDED)
echo ==============================================
echo.
echo 1. Go to: https://render.com/
echo 2. Sign up/login with GitHub
echo 3. Click "New +" then "Web Service"
echo 4. Connect your GitHub account
echo 5. Select "streaming-analytics-platform" repository
echo 6. Render auto-detects Docker and deploys!
echo.
echo 🎯 ALTERNATIVE: RAILWAY.APP
echo ===========================
echo.
echo 1. Go to: https://railway.app/
echo 2. Login with GitHub
echo 3. Click "New Project"
echo 4. Select "Deploy from GitHub repo"
echo 5. Choose your repository
echo 6. Railway auto-deploys!
echo.

echo ✅ AFTER DEPLOYMENT:
echo ====================
echo.
echo Your system will be live at:
echo - Render: https://your-app.onrender.com
echo - Railway: https://your-app.railway.app
echo.
echo Add these URLs to:
echo ✅ Your resume
echo ✅ LinkedIn profile
echo ✅ Portfolio website
echo ✅ GitHub repository description
echo.

set /p choice="Open GitHub to create repository? (y/n): "
if /i "%choice%"=="y" (
    start https://github.com/new
)

echo.
echo 🚀 Your streaming platform is ready to go live!
echo    Just follow the steps above - no CLI needed!
echo.
pause