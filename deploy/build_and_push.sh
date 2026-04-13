#!/bin/bash
set -e

REPO="us-central1-docker.pkg.dev/tickertape-493122/tickertape"
BACKEND_URL="https://tickertape-api-519484092009.us-central1.run.app/api"

echo "=== Building backend image (amd64) ==="
docker build --platform linux/amd64 -f Dockerfile.backend -t $REPO/backend:latest .

echo "=== Building frontend image (amd64) ==="
docker build --platform linux/amd64 -f Dockerfile.frontend.prod --build-arg VITE_API_URL=$BACKEND_URL -t $REPO/frontend:latest .

echo "=== Pushing images ==="
docker push $REPO/backend:latest
docker push $REPO/frontend:latest

echo "=== Done ==="
