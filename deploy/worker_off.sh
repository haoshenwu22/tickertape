#!/bin/bash
# Manually scale the worker DOWN (to save money when idle)
# min=0 means it scales to zero when no requests come in
gcloud run services update tickertape-worker --region=us-central1 --min-instances=0 --max-instances=1
echo "Worker scaled DOWN (min=0, max=1; will go idle when no requests)"
