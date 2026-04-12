# TickerTape

A web application for subscribing to stock price updates via email, with AI-powered Buy/Hold/Sell recommendations.

Built for the Hextom Software Engineer 2nd Round Take-Home Project.

## Project Status

### Completed
- [x] Project scaffolding (Django + React + Docker)
- [x] Authentication system (JWT, register/login, admin/regular user roles)
- [x] Subscription CRUD (create, list, delete with real ticker validation)
- [x] Stock price service (live Yahoo Finance data + mock fallback)
- [x] AI recommendation engine (Claude API with provider abstraction)
- [x] Email system (HTML templates, merge logic, Send Now, console backend for dev)
- [x] Periodic scheduling (Celery Beat — hourly Mon–Fri 9–5 ET)
- [x] Price alerts bonus feature (target price notifications)
- [x] Stock charts bonus feature (sparklines + interactive full charts)
- [x] Local development and testing

### Remaining
- [ ] Set up Gmail SMTP for real email delivery
- [ ] Deploy to GCP (Cloud Run + Cloud SQL + Secret Manager)
- [ ] Production environment configuration
- [ ] Final end-to-end testing on production

## Features

- **Stock Subscriptions** — Subscribe to stock tickers and receive periodic email updates with current prices
- **AI Recommendations** — Each stock includes a Buy/Hold/Sell recommendation with reasoning, powered by Claude AI
- **Email Merging** — Multiple subscriptions for the same email are merged into a single email
- **Periodic Scheduling** — Emails sent every hour, Mon–Fri, 9 AM–5 PM Eastern Time
- **Price Alerts** — Set target price alerts that trigger email notifications when conditions are met
- **Stock Charts** — Interactive sparklines and expandable historical charts (1W/1M/3M/1Y)
- **Role-Based Access** — Regular users see only their subscriptions; admins see all

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 6, Django REST Framework |
| Frontend | React 18 (Vite), Tailwind CSS 4 |
| Database | PostgreSQL 16 |
| Task Queue | Celery + Redis + django-celery-beat |
| Stock Data | Yahoo Finance (yfinance) |
| AI | Claude API (Haiku) with provider abstraction |
| Email | Gmail SMTP |
| Auth | JWT (djangorestframework-simplejwt) |

## Architecture

```
┌─────────────┐     ┌───────────────────────┐     ┌───────────┐
│  React SPA  │────▶│  Django REST API      │────▶│PostgreSQL │
│  (Vite)     │     │  - Auth (JWT)         │     └───────────┘
└─────────────┘     │  - Subscriptions CRUD │
                    │  - Stock Prices       │────▶ Yahoo Finance API
                    │  - AI Recommendations │────▶ Claude API
                    │  - Email Service      │────▶ Gmail SMTP
                    └──────────┬───────────┘
                               │
                    ┌──────────▼────────────┐
                    │  Celery Worker/Beat   │────▶ Redis
                    │  - Periodic emails    │
                    │  - Price alert checks │
                    └───────────────────────┘
```

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker & Docker Compose (for PostgreSQL and Redis)

### 1. Clone and configure environment

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

### 2. Start PostgreSQL and Redis

```bash
docker compose up db redis -d
```

### 3. Set up the Python backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser   # creates your admin account
```

### 4. Start the Django backend

```bash
# In backend/ directory, with venv activated
python manage.py runserver
```

Backend runs at `http://localhost:8000`.

### 5. Start the React frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 6. (Optional) Start Celery worker and beat

These are only needed for periodic email sending and automatic price alert checking. The core app works without them — "Send Now" triggers synchronously.

```bash
# Terminal 3 — Celery worker
cd backend
source ../venv/bin/activate
celery -A config worker -l info

# Terminal 4 — Celery beat scheduler
cd backend
source ../venv/bin/activate
celery -A config beat -l info
```

### 7. Open the app

Go to `http://localhost:5173` — register an account or log in with your superuser credentials.

## Environment Variables

| Variable | Description | Default | Required for Production |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | dev key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://postgres:postgres@localhost:5432/tickertape` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | Yes |
| `ANTHROPIC_API_KEY` | Claude API key for AI recommendations | — | Yes |
| `GMAIL_ADDRESS` | Gmail address for sending emails | — | Yes |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your regular password) | — | Yes |
| `EMAIL_BACKEND` | Django email backend | `console` (prints to terminal) | Set to `django.core.mail.backends.smtp.EmailBackend` for production |
| `AI_RECOMMENDATION_PROVIDER` | `claude` or `rule_based` | `claude` | No |
| `DEBUG` | Enable debug mode | `True` | Set to `False` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins | `http://localhost:5173` | Yes |
| `ALLOWED_HOSTS` | Django allowed hosts | `localhost,127.0.0.1` | Yes |

## Design Decisions

### Scheduling
- Emails sent at the top of each hour: 9:00, 10:00, ..., 17:00 ET (9 sends/day max)
- No market holiday awareness — deliberate simplification; Mon–Fri schedule as specified
- Idempotent: skips if no subscriptions exist

### AI Provider Abstraction
The recommendation engine uses a provider pattern (`recommendations/providers/`) to allow swapping AI models:
- **Claude** (default) — `claude-haiku-4-5-20251001` for fast, cheap, quality recommendations
- **Rule-based** — fallback if AI provider is unavailable (>3% up → Sell, >3% down → Buy, else Hold)
- To add a new provider (e.g., DeepSeek, Kimi): implement `RecommendationProvider` base class and register in `services.py`

### Email Merging
- Subscriptions are grouped by email address (not by user), so `user@example.com` subscribed to AAPL and BB receives one email with both
- Uses Django's `send_mail` with HTML template + plain-text fallback

### Authentication
- JWT tokens (access: 30 min, refresh: 7 days) stored in localStorage
- Django's built-in `is_staff` flag used as admin indicator — no custom user model fields needed
- Admin users see all subscriptions and alerts across all users

### Stock Data
- Primary: Yahoo Finance via `yfinance` library
- Mock fallback: returns hardcoded prices if yfinance is unavailable, flagged with `is_mock: true`

## Bonus Features

### 1. Price Alerts
Users can set target price alerts with "above" or "below" conditions. A Celery task checks prices every 15 minutes and sends email notifications when conditions are met. Alerts are marked as triggered and won't fire again.

**Value:** Provides immediate, actionable notifications instead of waiting for the hourly digest. Common request in financial apps.

### 2. Stock Charts
Interactive price charts using Recharts:
- Sparkline previews (7-day) in the subscription table
- Expandable full chart modal with 1W/1M/3M/1Y period selection
- Color-coded: green when trending up, red when trending down

**Value:** Visual context for price movements helps users quickly assess their portfolio without leaving the app.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login (returns JWT) |
| POST | `/api/auth/refresh/` | Refresh JWT token |
| GET | `/api/auth/me/` | Current user info |
| GET | `/api/subscriptions/` | List subscriptions |
| POST | `/api/subscriptions/` | Create subscription |
| DELETE | `/api/subscriptions/{id}/` | Delete subscription |
| POST | `/api/subscriptions/{id}/send-now/` | Send immediate email |
| GET | `/api/stocks/prices/?tickers=AAPL,BB` | Batch stock prices |
| GET | `/api/stocks/history/?ticker=AAPL&period=1mo` | Historical prices |
| GET | `/api/stocks/validate/?ticker=AAPL` | Validate ticker symbol |
| GET | `/api/alerts/` | List price alerts |
| POST | `/api/alerts/` | Create price alert |
| DELETE | `/api/alerts/{id}/` | Delete price alert |
