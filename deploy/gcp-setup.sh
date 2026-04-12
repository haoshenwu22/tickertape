#!/bin/bash
# TickerTape GCP Deployment Setup
# Run this script after: gcloud auth login && gcloud config set project YOUR_PROJECT_ID

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_ACCOUNT="tickertape-sa"

echo "=== TickerTape GCP Deployment ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# 1. Enable required APIs
echo "--- Enabling APIs ---"
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com

# 2. Create Artifact Registry repo
echo "--- Creating Artifact Registry ---"
gcloud artifacts repositories create tickertape \
  --repository-format=docker \
  --location=$REGION \
  --description="TickerTape Docker images" 2>/dev/null || echo "  (already exists)"

# 3. Create Cloud SQL Postgres instance
echo "--- Creating Cloud SQL instance ---"
gcloud sql instances create tickertape-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10 \
  --storage-type=SSD 2>/dev/null || echo "  (already exists)"

gcloud sql databases create tickertape \
  --instance=tickertape-db 2>/dev/null || echo "  (already exists)"

gcloud sql users set-password postgres \
  --instance=tickertape-db \
  --password="$(openssl rand -base64 24)"

# 4. Create secrets in Secret Manager
echo "--- Creating secrets ---"
echo "You will need to set these secret values manually:"
for SECRET in django-secret-key database-url redis-url anthropic-api-key gmail-address gmail-app-password; do
  gcloud secrets create $SECRET --replication-policy=automatic 2>/dev/null || echo "  $SECRET already exists"
done

echo ""
echo "=== Next Steps ==="
echo "1. Set secret values:"
echo "   echo -n 'YOUR_VALUE' | gcloud secrets versions add django-secret-key --data-file=-"
echo "   echo -n 'YOUR_VALUE' | gcloud secrets versions add anthropic-api-key --data-file=-"
echo "   echo -n 'YOUR_VALUE' | gcloud secrets versions add gmail-address --data-file=-"
echo "   echo -n 'YOUR_VALUE' | gcloud secrets versions add gmail-app-password --data-file=-"
echo ""
echo "2. Get the Cloud SQL connection name:"
echo "   gcloud sql instances describe tickertape-db --format='value(connectionName)'"
echo ""
echo "3. Set the DATABASE_URL secret (format: postgres://postgres:PASSWORD@/tickertape?host=/cloudsql/CONNECTION_NAME)"
echo ""
echo "4. Run deploy.sh to build and deploy"
