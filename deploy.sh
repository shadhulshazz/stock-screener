#!/bin/bash
# Deploy Stock Screener to Google Cloud Run

set -e

echo "🚀 Stock Screener - Google Cloud Run Deployment"
echo "================================================"

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="stock-screener"
REGION="us-central1"

echo "📍 Project ID: $PROJECT_ID"
echo "📍 Service: $SERVICE_NAME"
echo "📍 Region: $REGION"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create it from .env.example"
    exit 1
fi

echo "\n📦 Building container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "\n🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --memory 512Mi \
    --timeout 540 \
    --env-vars-file .env.cloud

echo "\n⏰ Setting up Cloud Scheduler..."
# Create scheduler job (runs at 8:45 AM IST every weekday)
gcloud scheduler jobs create pubsub stock-screener-daily \
    --location=$REGION \
    --schedule="45 8 * * 1-5" \
    --time-zone="Asia/Kolkata" \
    --topic stock-screener \
    --message-body '{}' \
    2>/dev/null || echo "Job already exists"

echo "\n✅ Deployment complete!"
echo "\nNext steps:"
echo "1. Update .env.cloud with your API keys"
echo "2. Monitor logs: gcloud run logs read $SERVICE_NAME --region=$REGION"
echo "3. Trigger manually: gcloud scheduler jobs run stock-screener-daily --location=$REGION"
