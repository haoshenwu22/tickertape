#!/bin/bash
# DELETE everything - this is irreversible!
REGION="us-central1"

echo "⚠️  This will permanently delete ALL GCP resources for TickerTape."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "=== Deleting Cloud Run services ==="
gcloud run services delete tickertape-api --region=$REGION --quiet
gcloud run services delete tickertape-worker --region=$REGION --quiet
gcloud run services delete tickertape-web --region=$REGION --quiet

echo "=== Deleting Cloud Run jobs ==="
gcloud run jobs delete tickertape-migrate --region=$REGION --quiet 2>/dev/null
gcloud run jobs delete tickertape-admin --region=$REGION --quiet 2>/dev/null

echo "=== Deleting Cloud SQL ==="
gcloud sql instances delete tickertape-db --quiet

echo "=== Deleting Redis ==="
gcloud redis instances delete tickertape-redis --region=$REGION --quiet

echo "=== Deleting VPC Connector ==="
gcloud compute networks vpc-access connectors delete tickertape-connector --region=$REGION --quiet

echo "=== Deleting Artifact Registry ==="
gcloud artifacts repositories delete tickertape --location=$REGION --quiet

echo "=== Deleting Secrets ==="
gcloud secrets delete django-secret-key --quiet
gcloud secrets delete database-url --quiet
gcloud secrets delete redis-url --quiet
gcloud secrets delete anthropic-api-key --quiet
gcloud secrets delete gmail-address --quiet
gcloud secrets delete gmail-app-password --quiet

echo ""
echo "=== All resources deleted. Monthly cost: $0 ==="
