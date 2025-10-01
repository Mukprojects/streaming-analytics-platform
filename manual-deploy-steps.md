# 🚀 Manual Deployment Steps for Windows

## 📋 **Step-by-Step Railway Deployment**

### **Step 1: Install Prerequisites**
```cmd
# Install Node.js from https://nodejs.org/
# Then install Railway CLI
npm install -g @railway/cli
```

### **Step 2: Login to Railway**
```cmd
# This will open your browser
railway login
```

### **Step 3: Create New Project**
```cmd
# Create new Railway project
railway new
```

### **Step 4: Set Environment Variables**
```cmd
railway variables set REDIS_HOST=redis
railway variables set STREAM_KEY=events
railway variables set RATE=100
railway variables set CONSUMER_GROUP=event_group
railway variables set AGG_KEY=aggregates
railway variables set METRICS_PORT=8000
railway variables set PORT=8080
```

### **Step 5: Prepare Deployment**
```cmd
# Copy the Railway deployment config
copy deployment\railway-deploy.yml docker-compose.yml
```

### **Step 6: Deploy**
```cmd
# Deploy your application
railway up
```

### **Step 7: Get Your URL**
```cmd
# Check deployment status and get URL
railway status
```

## 🌐 **Alternative: Web-Based Deployment**

### **Option 1: GitHub + Railway Integration**
1. **Push to GitHub**:
   ```cmd
   git init
   git add .
   git commit -m "Add streaming pipeline"
   git remote add origin https://github.com/yourusername/streaming-pipeline
   git push -u origin main
   ```

2. **Connect to Railway**:
   - Go to https://railway.app/
   - Click "Deploy from GitHub"
   - Select your repository
   - Railway will auto-deploy!

### **Option 2: Render.com (Alternative)**
1. **Push to GitHub** (same as above)
2. **Go to Render.com**:
   - Connect GitHub account
   - Create new "Web Service"
   - Select your repository
   - Use `deployment/render-deploy.yml`

### **Option 3: Heroku**
```cmd
# Install Heroku CLI from https://devcenter.heroku.com/articles/heroku-cli
heroku create your-streaming-pipeline
heroku addons:create heroku-redis:mini
git push heroku main
```

## 🎯 **Expected Results**

After deployment, you'll have:
- **Live System**: `https://your-app.railway.app`
- **Grafana**: `https://your-app.railway.app:3000`
- **Prometheus**: `https://your-app.railway.app:9090`
- **API**: `https://your-app.railway.app:8080/aggregates`

## 🔧 **Troubleshooting**

### **If Railway CLI fails:**
```cmd
# Try alternative installation
npm install -g @railway/cli --force
```

### **If deployment fails:**
```cmd
# Check logs
railway logs

# Redeploy
railway up --detach
```

### **If services don't start:**
- Check Railway dashboard for logs
- Verify environment variables are set
- Try redeploying with `railway up`

## 🎨 **After Deployment**

1. **Update Portfolio Landing Page**:
   - Edit `deployment/portfolio-landing.html`
   - Replace `your-app.railway.app` with your actual URL

2. **Create GitHub Repository**:
   - Use `portfolio-README.md` as your README
   - Add live demo links

3. **Update Resume/LinkedIn**:
   - Add: "Live Streaming Analytics Platform - [your-url]"
   - Mention: "Production system processing 500+ events/sec"

## 🚀 **Quick Commands Summary**

```cmd
# Complete deployment in one go
npm install -g @railway/cli
railway login
railway new
railway variables set REDIS_HOST=redis RATE=100 PORT=8080
copy deployment\railway-deploy.yml docker-compose.yml
railway up
railway status
```

**Your streaming pipeline will be live and ready for your portfolio!** 🎯