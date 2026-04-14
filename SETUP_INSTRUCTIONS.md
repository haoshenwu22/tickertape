# Setup & Run Instructions

Complete instructions for running TickerTape locally and deploying to GCP.

---

## Live Demo

- **Frontend**: https://tickertape-web-519484092009.us-central1.run.app
- **Backend API**: https://tickertape-api-519484092009.us-central1.run.app
- **Django Admin Panel**: https://tickertape-api-519484092009.us-central1.run.app/admin/

To try the app without setup: register a new account on the frontend URL, verify your email, and start subscribing to tickers.

---

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker & Docker Compose (for PostgreSQL and Redis)
- An Anthropic API key (https://console.anthropic.com)

### Step 1: Clone and configure environment

```bash
git clone <repo-url>
cd tickertape
cp .env.example .env
```

Edit `.env` and set your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...your-key...
```

All other defaults work out of the box for local development. Emails will print to the Django console (no Gmail credentials needed for dev).

### Step 2: Start PostgreSQL and Redis via Docker

```bash
docker compose up db redis -d
```

### Step 3: Set up the Python backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser   # creates your admin account
```

### Step 4: Start the Django backend

```bash
# In backend/ directory, with venv activated
python manage.py runserver
```

Backend runs at `http://localhost:8000`. Admin panel at `http://localhost:8000/admin/`.

### Step 5: Start the React frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Step 6 (optional): Start Celery worker and beat

Needed for periodic email sending, price alert checking, and async verification emails. The core app works without them — "Send Now" triggers synchronously.

```bash
# Terminal 3 — Celery worker + beat
cd backend
source ../venv/bin/activate
celery -A config worker --beat -l info
```

### Step 7: Open the app

Go to `http://localhost:5173` — register a new account (verification email prints to the Django console in dev mode; copy the verify link from there to complete registration).

---

## Running the Full Stack via Docker Compose

If you prefer to run everything (backend, frontend, worker, Postgres, Redis) with one command:

```bash
docker compose up --build
```

This brings up:
- PostgreSQL 16
- Redis 7
- Django backend (port 8000)
- React frontend (port 5173)
- Celery worker + beat

Requires `.env` with `ANTHROPIC_API_KEY` set.

---

## Environment Variables

| Variable | Description | Default | Required for Production |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | dev key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://postgres:postgres@localhost:5432/tickertape` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | Yes |
| `ANTHROPIC_API_KEY` | Claude API key for AI recommendations | - | Yes |
| `GMAIL_ADDRESS` | Gmail address for sending emails | - | Yes |
| `GMAIL_APP_PASSWORD` | Gmail App Password | - | Yes |
| `EMAIL_BACKEND` | Django email backend | `console` | `django.core.mail.backends.smtp.EmailBackend` |
| `AI_RECOMMENDATION_PROVIDER` | `claude` or `rule_based` | `claude` | No |
| `FRONTEND_URL` | Frontend URL for verification links | `http://localhost:5173` | Yes |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `http://localhost:8000` | Yes |
| `DEBUG` | Enable debug mode | `True` | Set to `False` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins | `http://localhost:5173` | Yes |

---

## Gmail SMTP Setup (for real email delivery)

For local dev, emails print to the Django console by default — no Gmail setup needed. For production (or to test real email delivery locally), set up Gmail App Password:

1. Enable 2-Step Verification on your Gmail account: https://myaccount.google.com/signinandsecurity
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Set in `.env`:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-16-char-app-password
   ```

---

## Production Deployment (GCP)

### Prerequisites
- GCP account with billing enabled
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- Docker Desktop running (for building images)

### One-time GCP project setup

```bash
# Set active project (create one in the GCP console first)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  cloudbuild.googleapis.com

# Grant Cloud Run service account access to secrets
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Infrastructure setup (one-time)

```bash
# Create Cloud SQL (PostgreSQL 16)
gcloud sql instances create tickertape-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=us-central1 --storage-size=10 --storage-type=SSD --edition=enterprise
gcloud sql databases create tickertape --instance=tickertape-db
gcloud sql users set-password postgres --instance=tickertape-db --password=STRONG_PASSWORD

# Create Memorystore Redis
gcloud redis instances create tickertape-redis --size=1 --region=us-central1 --redis-version=redis_7_0 --tier=basic

# Create VPC Connector (required for Cloud Run → Memorystore)
gcloud compute networks vpc-access connectors create tickertape-connector --region=us-central1 --range=10.8.0.0/28

# Create Artifact Registry
gcloud artifacts repositories create tickertape --repository-format=docker --location=us-central1
gcloud auth configure-docker us-central1-docker.pkg.dev

# Create secrets in Secret Manager
echo -n 'YOUR_DJANGO_SECRET_KEY' | gcloud secrets create django-secret-key --data-file=-
echo -n 'postgres://postgres:STRONG_PASSWORD@/tickertape?host=/cloudsql/YOUR_PROJECT:us-central1:tickertape-db' | gcloud secrets create database-url --data-file=-
echo -n 'redis://REDIS_IP:6379/0' | gcloud secrets create redis-url --data-file=-
echo -n 'YOUR_ANTHROPIC_API_KEY' | gcloud secrets create anthropic-api-key --data-file=-
echo -n 'your-email@gmail.com' | gcloud secrets create gmail-address --data-file=-
echo -n 'your-gmail-app-password' | gcloud secrets create gmail-app-password --data-file=-
```

Replace `YOUR_PROJECT_ID`, `YOUR_PROJECT`, `STRONG_PASSWORD`, `REDIS_IP`, `YOUR_DJANGO_SECRET_KEY`, `YOUR_ANTHROPIC_API_KEY` with actual values. Get `REDIS_IP` via `gcloud redis instances describe tickertape-redis --region=us-central1 --format='value(host)'`.

### Deploy the app

```bash
# Build Docker images (cross-compile for amd64) and push to Artifact Registry
bash deploy/build_and_push.sh

# Deploy all Cloud Run services + run migrations
bash deploy/deploy_cloudrun.sh
```

### Create an admin user in production

```bash
gcloud run jobs create tickertape-admin \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/tickertape/backend:latest \
  --region=us-central1 \
  --set-cloudsql-instances=YOUR_PROJECT_ID:us-central1:tickertape-db \
  --vpc-connector=projects/YOUR_PROJECT_ID/locations/us-central1/connectors/tickertape-connector \
  --set-secrets=DJANGO_SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --set-env-vars=DJANGO_SUPERUSER_USERNAME=admin,DJANGO_SUPERUSER_EMAIL=you@example.com,DJANGO_SUPERUSER_PASSWORD=YOUR_ADMIN_PASSWORD \
  --command=python --args=manage.py,createsuperuser,--noinput \
  --execute-now --wait
```

### Day-to-day deployment scripts

| Script | Purpose |
|---|---|
| `deploy/build_and_push.sh` | Build and push Docker images |
| `deploy/deploy_cloudrun.sh` | Full Cloud Run deployment |
| `deploy/pause_services.sh` | Pause services to reduce billing (~$1.35/day floor) |
| `deploy/resume_services.sh` | Resume paused services |
| `deploy/destroy_all.sh` | Delete all GCP resources ($0/day) |

---

## Running Tests

```bash
cd backend
source ../venv/bin/activate
python manage.py test
```

---

## Troubleshooting

**"Docker daemon not running"** — Open Docker Desktop and wait for the whale icon to stop animating.

**"module 'django' not found"** — You're not in the virtual environment. Run `source venv/bin/activate`.

**"Permission denied on secret"** — The Cloud Run service account needs the `roles/secretmanager.secretAccessor` role. Run the IAM binding command from "One-time GCP project setup".

**"CSRF verification failed" on Django admin** — Set `CSRF_TRUSTED_ORIGINS` env var to the backend's public URL.

**Verification email slow** — It's sent via Celery (async). In production, the Celery worker has cold-start latency. Check the Cloud Run worker logs.

**"Cloud Run does not support image ... must support amd64/linux"** — On Apple Silicon Macs, Docker builds ARM images by default. Use `--platform linux/amd64` flag (already in deploy scripts).
