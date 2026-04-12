#!/bin/bash
# TickerTape Cloud Run Deployment
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO="$REGION-docker.pkg.dev/$PROJECT_ID/tickertape"

echo "=== Building and Deploying TickerTape ==="
echo "Project: $PROJECT_ID"
echo "Registry: $REPO"
echo ""

# 1. Build backend image
echo "--- Building backend image ---"
docker build -f Dockerfile.backend -t $REPO/backend:latest .
docker push $REPO/backend:latest

# 2. Build frontend image
echo "--- Building frontend image ---"
docker build -f Dockerfile.frontend.prod -t $REPO/frontend:latest ./frontend
docker push $REPO/frontend:latest

# 3. Get Cloud SQL connection name
SQL_CONNECTION=$(gcloud sql instances describe tickertape-db --format='value(connectionName)')

# 4. Deploy backend API
echo "--- Deploying backend API ---"
gcloud run deploy tickertape-api \
  --image=$REPO/backend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances=$SQL_CONNECTION \
  --set-secrets=DJANGO_SECRET_KEY=django-secret-key:latest \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=REDIS_URL=redis-url:latest \
  --set-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest \
  --set-secrets=GMAIL_ADDRESS=gmail-address:latest \
  --set-secrets=GMAIL_APP_PASSWORD=gmail-app-password:latest \
  --set-env-vars=DEBUG=False,EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3

# 5. Get backend URL
BACKEND_URL=$(gcloud run services describe tickertape-api --region=$REGION --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"

# 6. Deploy frontend
echo "--- Deploying frontend ---"
gcloud run deploy tickertape-web \
  --image=$REPO/frontend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=BACKEND_URL=$BACKEND_URL \
  --memory=256Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2

FRONTEND_URL=$(gcloud run services describe tickertape-web --region=$REGION --format='value(status.url)')

# 7. Update CORS to allow frontend URL
echo "--- Updating CORS ---"
gcloud run services update tickertape-api \
  --region=$REGION \
  --update-env-vars=CORS_ALLOWED_ORIGINS=$FRONTEND_URL,ALLOWED_HOSTS=$(echo $BACKEND_URL | sed 's|https://||')

# 8. Run migrations
echo "--- Running migrations ---"
gcloud run jobs create tickertape-migrate \
  --image=$REPO/backend:latest \
  --region=$REGION \
  --set-secrets=DJANGO_SECRET_KEY=django-secret-key:latest \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=REDIS_URL=redis-url:latest \
  --add-cloudsql-instances=$SQL_CONNECTION \
  --command="python,manage.py,migrate" \
  --execute-now 2>/dev/null || \
gcloud run jobs update tickertape-migrate \
  --image=$REPO/backend:latest \
  --region=$REGION \
  --execute-now

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "To create an admin user:"
echo "  gcloud run jobs create tickertape-admin --image=$REPO/backend:latest --region=$REGION --add-cloudsql-instances=$SQL_CONNECTION --set-secrets=... --command='python,manage.py,createsuperuser,--noinput' --set-env-vars=DJANGO_SUPERUSER_USERNAME=admin,DJANGO_SUPERUSER_EMAIL=admin@tickertape.app,DJANGO_SUPERUSER_PASSWORD=YOUR_PASSWORD --execute-now"
