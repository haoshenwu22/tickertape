#!/bin/bash
# Pause all services to stop billing (keeps resources, just stops them)
REGION="us-central1"

echo "=== Scaling Cloud Run to zero ==="
gcloud run services update tickertape-api --region=$REGION --min-instances=0 --max-instances=0
gcloud run services update tickertape-worker --region=$REGION --min-instances=0 --max-instances=0
gcloud run services update tickertape-web --region=$REGION --min-instances=0 --max-instances=0

echo ""
echo "=== Stopping Cloud SQL ==="
gcloud sql instances patch tickertape-db --activation-policy=NEVER

echo ""
echo "=== Done - services paused ==="
echo "Cloud Run: scaled to 0 (no charges)"
echo "Cloud SQL: stopped (no compute charges, small storage charge ~$0.17/mo)"
echo "Redis & VPC: still running (~$7/mo) - these can't be paused, only deleted"
echo ""
echo "To resume: bash deploy/resume_services.sh"
