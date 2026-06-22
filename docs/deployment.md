# Deployment Guide - Google Cloud Run

## Architecture

```
Cloud Scheduler (Cron)
        ↓
   Pub/Sub Topic
        ↓
  Cloud Run Service
        ↓
   Telegram Bot / Sheets
```

## Prerequisites

- Google Cloud Account with billing enabled
- `gcloud` CLI installed
- Docker (optional for local testing)

## Step 1: Setup Google Cloud Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable scheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 2: Prepare Deployment

```bash
# Create .env.cloud file with production secrets
cp .env.example .env.cloud

# Edit with production values
nano .env.cloud
```

## Step 3: Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Step 4: Verify Deployment

```bash
# Check Cloud Run service
gcloud run services list

# View logs
gcloud run logs read stock-screener --limit 50

# Manual trigger
gcloud scheduler jobs run stock-screener-daily --location=us-central1
```

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud run logs read stock-screener --follow

# Last 100 lines
gcloud run logs read stock-screener --limit 100
```

### Set Up Alerts

1. Go to Cloud Run service
2. Click "Metrics"
3. Set up error rate alerts in Cloud Console

## Costs

Free tier covers:
- 2M requests/month
- 360K GB-seconds/month
- Daily screening = ~100 requests/month

**Estimated monthly cost: $0** (within free tier)

## Troubleshooting

### Service fails to deploy

```bash
# Check build logs
gcloud builds log <build-id>

# Common issues: missing dependencies, timeout
```

### Scheduler job not triggering

```bash
# Verify job exists
gcloud scheduler jobs list

# Check job history
gcloud scheduler jobs describe stock-screener-daily
```

### Credentials error

- Ensure `GOOGLE_SHEETS_CREDENTIALS` file exists locally
- Upload to Cloud Secrets Manager:
  ```bash
  gcloud secrets create sheets-creds --data-file=credentials.json
  ```

## Auto-Scaling

Default Cloud Run settings:
- Min instances: 0 (scales to zero when not running)
- Max instances: 10
- Memory: 512 MB
- Timeout: 540 seconds (9 minutes)

Adjust in `deploy.sh` as needed.
