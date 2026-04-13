#!/bin/bash
set -e

REPO="us-central1-docker.pkg.dev/tickertape-493122/tickertape"
REGION="us-central1"
SQL_CONNECTION="tickertape-493122:us-central1:tickertape-db"
VPC_CONNECTOR="projects/tickertape-493122/locations/us-central1/connectors/tickertape-connector"
BACKEND_URL=$(gcloud run services describe tickertape-api --region=$REGION --format='value(status.url)')

echo "Backend URL: $BACKEND_URL"

echo ""
echo "=== Step 3: Deploy Celery worker ==="
gcloud run deploy tickertape-worker --image=$REPO/backend:latest --region=$REGION --platform=managed --no-allow-unauthenticated --add-cloudsql-instances=$SQL_CONNECTION --vpc-connector=$VPC_CONNECTOR --set-secrets=DJANGO_SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,GMAIL_ADDRESS=gmail-address:latest,GMAIL_APP_PASSWORD=gmail-app-password:latest --set-env-vars=DEBUG=False,EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend --memory=512Mi --cpu=1 --min-instances=1 --max-instances=1 --no-cpu-throttling --command=bash --args=worker_entrypoint.sh

echo ""
echo "=== Step 4: Deploy frontend ==="
gcloud run deploy tickertape-web --image=$REPO/frontend:latest --region=$REGION --platform=managed --allow-unauthenticated --set-env-vars=BACKEND_URL=$BACKEND_URL --memory=256Mi --cpu=1 --min-instances=0 --max-instances=2 --port=8080

echo ""
echo "=== Step 5: Update CORS ==="
FRONTEND_URL=$(gcloud run services describe tickertape-web --region=$REGION --format='value(status.url)')
gcloud run services update tickertape-api --region=$REGION --update-env-vars=CORS_ALLOWED_ORIGINS=$FRONTEND_URL

echo ""
echo "=== Step 6: Run migrations ==="
gcloud run jobs create tickertape-migrate --image=$REPO/backend:latest --region=$REGION --add-cloudsql-instances=$SQL_CONNECTION --vpc-connector=$VPC_CONNECTOR --set-secrets=DJANGO_SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest --set-env-vars=DEBUG=False --command=python --args=manage.py,migrate --execute-now --wait

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "Next: Create admin user by setting DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD env vars and running manage.py createsuperuser --noinput"
