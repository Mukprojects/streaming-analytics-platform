#!/bin/bash

# 🚀 Deploy Streaming Pipeline to Railway.app
# One-click deployment script for portfolio demonstration

echo "🚀 DEPLOYING STREAMING PIPELINE TO RAILWAY"
echo "=========================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Create new Railway project
echo "📦 Creating new Railway project..."
railway new

# Set up environment variables
echo "⚙️ Setting up environment variables..."
railway variables set REDIS_HOST=redis
railway variables set STREAM_KEY=events
railway variables set RATE=100
railway variables set CONSUMER_GROUP=event_group
railway variables set AGG_KEY=aggregates
railway variables set METRICS_PORT=8000
railway variables set PORT=8080

# Copy deployment configuration
echo "📋 Preparing deployment configuration..."
cp deployment/railway-deploy.yml docker-compose.yml

# Deploy the application
echo "🚀 Deploying application..."
railway up

# Get the deployment URL
echo "🔗 Getting deployment URL..."
RAILWAY_URL=$(railway status --json | jq -r '.deployments[0].url')

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================"
echo ""
echo "🎯 Your streaming pipeline is now live at:"
echo "🔗 Main App: $RAILWAY_URL"
echo "📊 Grafana: $RAILWAY_URL:3000 (admin/demo123)"
echo "📈 Prometheus: $RAILWAY_URL:9090"
echo "🔌 API: $RAILWAY_URL:8080/aggregates"
echo ""
echo "💡 Add these URLs to your portfolio and resume!"
echo "🎨 Customize the landing page in deployment/portfolio-landing.html"
echo ""
echo "🎯 Next Steps:"
echo "1. Update portfolio-landing.html with your Railway URL"
echo "2. Create GitHub repository with impressive README"
echo "3. Add live demo links to LinkedIn and resume"
echo "4. Share on social media with #BuildInPublic"
echo ""
echo "🚀 Your portfolio just got a major upgrade!"