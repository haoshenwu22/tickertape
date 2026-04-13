#!/bin/bash
# Resume all paused services
REGION="us-central1"

echo "=== Starting Cloud SQL ==="
gcloud sql instances patch tickertape-db --activation-policy=ALWAYS

echo ""
echo "=== Scaling Cloud Run back up ==="
gcloud run services update tickertape-api --region=$REGION --min-instances=0 --max-instances=3
gcloud run services update tickertape-worker --region=$REGION --min-instances=1 --max-instances=1
gcloud run services update tickertape-web --region=$REGION --min-instances=0 --max-instances=2

echo ""
echo "=== Done - services resumed ==="
