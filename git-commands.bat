@echo off
echo ========================================
echo 📋 GIT COMMANDS FOR DEPLOYMENT
echo ========================================
echo.
echo Copy and paste these commands ONE BY ONE:
echo.

echo 1. Initialize Git repository:
echo    git init
echo.

echo 2. Add all files:
echo    git add .
echo.

echo 3. Create first commit:
echo    git commit -m "Add streaming analytics platform"
echo.

echo 4. Set main branch:
echo    git branch -M main
echo.

echo 5. Add GitHub remote (REPLACE YOURUSERNAME):
echo    git remote add origin https://github.com/YOURUSERNAME/streaming-analytics-platform
echo.

echo 6. Push to GitHub:
echo    git push -u origin main
echo.

echo ========================================
echo 🎯 AFTER PUSHING TO GITHUB:
echo ========================================
echo.
echo Deploy on Render.com:
echo 1. Go to https://render.com/
echo 2. Login with GitHub
echo 3. New Web Service
echo 4. Connect your repo
echo 5. Auto-deploy!
echo.
echo OR deploy on Railway.app:
echo 1. Go to https://railway.app/
echo 2. Login with GitHub  
echo 3. New Project from GitHub
echo 4. Select your repo
echo 5. Auto-deploy!
echo.

echo 🚀 Your streaming platform will be LIVE!
echo.
pause