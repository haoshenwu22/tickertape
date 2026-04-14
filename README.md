# TickerTape

A web application for subscribing to stock price updates via email, with AI-powered Buy/Hold/Sell recommendations.

Built for the Hextom Software Engineer 2nd Round Take-Home Project.

**Live Demo:** https://tickertape-web-519484092009.us-central1.run.app
**Admin Panel:** https://tickertape-api-519484092009.us-central1.run.app/admin/

## Documents in this repo

| File | Purpose |
|---|---|
| `README.md` (this file) | Design notes, key assumptions, tradeoffs, important decisions |
| `SETUP_INSTRUCTIONS.md` | How to run locally and deploy to GCP |
| `AI_USAGE.md` | How AI was used in this project (prompts, corrections, verification) |
| `REQUIREMENTS_CHECKLIST.md` | Mapping of PDF requirements → implementation status |
| `DEVELOPMENT_LOG.md` | Chronological log of all bugs encountered and how they were resolved |

---

## Features Overview

- Stock subscriptions with real ticker validation (via yfinance)
- AI-generated Buy/Hold/Sell recommendations (Claude API, with provider abstraction)
- Email verification on registration (blocking) and on subscription emails
- Email merging — one email per recipient containing all their tickers
- Periodic sending hourly Mon-Fri 9-5 ET (Celery Beat)
- Price alerts with above/below conditions (bonus feature)
- Interactive stock charts — sparklines + full chart modal (bonus feature)
- Role-based access (regular users vs admins)
- Django admin panel for database management

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | Python 3.12 + Django 6 + DRF | Required by spec. DRF adds clean REST patterns + JWT support. |
| Frontend | React 18 + Vite + Tailwind CSS 4 | Required by spec. Vite's fast HMR and build speed was an easy choice over CRA. |
| Database | PostgreSQL 16 | Required by spec. |
| Task Queue | Celery + Redis | Mature, fits the once-per-hour scheduling requirement. `django-celery-beat` for the cron scheduler. |
| Stock Data | `yfinance` | Required by spec. Mock fallback for resilience. |
| AI | Claude API (Haiku) | Cheapest + fastest Claude model, sufficient for 1-sentence recommendations. |
| Email | Gmail SMTP (async via Celery) | Free, sufficient for demo. SendGrid/SES is the obvious upgrade for real scale. |
| Auth | JWT (`djangorestframework-simplejwt`) + custom email verification | JWT for SPA statelessness; email verification bolted on for security. |
| Deployment | GCP (Cloud Run + Cloud SQL + Memorystore + Secret Manager) | Managed services to minimize ops overhead for a demo project. |

---

## Architecture

```
┌─────────────┐     ┌───────────────────────┐     ┌───────────┐
│  React SPA  │────▶│  Django REST API      │────▶│PostgreSQL │
│  (Vite)     │     │  - Auth (JWT)         │     │(Cloud SQL)│
└─────────────┘     │  - Email Verification │     └───────────┘
  Cloud Run         │  - Subscriptions CRUD │
                    │  - Stock Prices       │────▶ Yahoo Finance API
                    │  - AI Recommendations │────▶ Claude API
                    │  - Email Service      │────▶ Gmail SMTP
                    └──────────┬───────────-┘
                     Cloud Run │
                    ┌──────────▼────────────┐     ┌───────────┐
                    │  Celery Worker/Beat   │────▶│   Redis   │
                    │  - Periodic emails    │     │(Memorystore)
                    │  - Price alert checks │     └───────────┘
                    │  - Verification emails│
                    └───────────────────────┘
                      Cloud Run
```

The backend API, Celery worker, and frontend each run as independent Cloud Run services. Secrets come from Secret Manager at container start. Redis lives in Memorystore reachable via a VPC connector.

---

## Key Assumptions

These are the things we assumed about the problem where the spec was silent. Each assumption trades off something.

### 1. "Email address" in a subscription is the recipient, not always the subscriber's email
The spec is ambiguous about whether the email in a subscription is always the logged-in user's email. We assumed the user can enter **any** email — but that opened an abuse vector (any user could spam any email address). We resolved this with email ownership verification: using a non-verified email triggers a verification flow for that address before the subscription activates.

### 2. "Merge emails when possible" applies to both scheduled and manual sends
The spec only explicitly calls out merging for periodic emails. We interpreted the intent as "a recipient should receive one email per send event, not N emails" — so Send Now also merges all of the recipient's active subscriptions. If the interviewer expected Send Now to be single-ticker, it's a one-line change to revert.

### 3. Market holidays aren't special
The schedule is "hourly Mon-Fri 9-5 ET." We do not check the NYSE holiday calendar. On a market holiday the app still sends emails — the recommendations will just reflect the previous trading day's data. Adding a holiday-aware check is a pure extension, not a bug.

### 4. Admins are fully trusted
Admins (Django's `is_staff=True`) bypass email verification entirely and can create subscriptions with any email. The assumption is that admins are internal staff, not customers. A more paranoid model would still require verification for admin-created emails targeting external users.

### 5. Recommendations are cached per ticker, not per user
Two users subscribed to AAPL will receive the same recommendation text within a 1-hour window. This is intentional — the recommendation is about the stock, not the user, and this avoids burning money on duplicate Claude API calls. The 1-hour TTL also matches the sending cadence.

### 6. Scale is modest
The app is designed for dozens to low thousands of users. Scaling to 10x or 100x is discussed in "Scaling Considerations" below — most of the architecture holds, but a few pieces (Gmail SMTP, Memorystore tier, Celery beat singleton) would need replacement.

---

## Important Decisions & Tradeoffs

### AI recommendation: provider abstraction
**Decision:** The recommendation engine has a `RecommendationProvider` base class (see `backend/recommendations/providers/base.py`). Swapping models (Claude → DeepSeek → Kimi → rule-based) is one new file implementing the base class.

**Why:** Lets us hedge against AI provider outages, pricing changes, and model deprecation. Also means it's trivial to drop in a smaller/cheaper model if usage grows.

**Tradeoff:** Slight complexity overhead vs just calling `anthropic.Anthropic()` inline. Worth it because we also get a built-in rule-based fallback when the Claude API fails.

### Email verification is blocking
**Decision:** Newly registered users cannot log in until they verify their email. Subscriptions to unverified emails are "pending" and don't receive any sending until verification.

**Why:** Without this, anyone could spam-subscribe others' inboxes with stock emails. Blocking verification is the standard modern pattern and is what users expect.

**Tradeoff:** Slower onboarding, and if Gmail SMTP is flaky the user is stuck. We mitigated by sending verification emails asynchronously (Celery) so the API response is fast, and added a "resend verification" button.

### Verification requires a manual button click
**Decision:** The verification page does NOT auto-verify on page load. The user must click a "Verify Email" button.

**Why:** Email clients (Gmail in particular) run link scanners that GET the verification URL to scan for malware. If the page had auto-verify, any email client or corporate security proxy could accidentally verify the account. This actually happened during development — a user's account was silently activated before the verification email even arrived in their inbox.

**Tradeoff:** One extra click for the user. Worth it — the alternative broke the entire security model.

### Celery worker is always-on (`min-instances=1`)
**Decision:** The Celery worker Cloud Run service has `min-instances=1` and `cpu-throttling=false`.

**Why:** Celery Beat is the scheduler — it must be running 24/7 to fire jobs at 9:00, 10:00, etc. Eastern Time. If the container sleeps, the schedule misses.

**Tradeoff:** This is the single biggest cost driver (~$2/day). A production rearchitecture would replace Celery Beat with Cloud Scheduler → Cloud Run Job, allowing the worker to scale to zero. For a demo, the simplicity won.

### `is_active` defaults to `False` on Subscription model
**Decision:** The model field is `is_active = BooleanField(default=False)`. Code paths that should create active subscriptions (admin, verified email) pass `is_active=True` explicitly.

**Why:** Fail-safe — any code path that forgets to set `is_active` creates a pending (safe) subscription, not an accidentally-active one. We learned this the hard way during testing.

**Tradeoff:** Slightly more verbose code (always pass the flag explicitly). Worth it for safety.

### Subscription visibility is email-based, not user-based
**Decision:** A user sees subscriptions where `user=me` OR `email IN my_verified_emails`.

**Why:** If someone else (or admin) creates a subscription targeting user A's email, user A should be able to see and delete it — otherwise they'd have to contact support.

**Tradeoff:** Users see subscriptions they didn't create, which could be confusing. Mitigated by the UI showing the email each subscription targets.

### React frontend calls the backend directly (no Nginx proxy)
**Decision:** The frontend container serves static files via Nginx with no `/api/` proxy. The React app has the backend URL baked in at build time via `VITE_API_URL`.

**Why:** We initially tried an Nginx proxy in the frontend container, which caused 502 errors due to SSL termination and host header issues between Cloud Run services. Direct calls with CORS are simpler and more reliable.

**Tradeoff:** CORS configuration needs to match production URLs exactly. A rebuild is needed if the backend URL changes (rare).

### JWT tokens in localStorage
**Decision:** Access token in localStorage, refresh token also in localStorage. Bearer auth via Authorization header.

**Why:** Simplest pattern for a SPA. DRF-simplejwt handles the server side.

**Tradeoff:** XSS risk — any JS can read the tokens. HttpOnly cookies would be safer but come with CSRF complexity. For a demo project, the simpler approach is fine; for real production with sensitive data, we'd switch to HttpOnly refresh cookie + short-lived access token in memory.

---

## Scaling Considerations

If this app had to scale to **10x or 100x users**:

- **Backend API** — Cloud Run auto-scales horizontally already. `max-instances` would need to be raised from 3.
- **Cloud SQL** — upgrade from db-f1-micro to a real tier, add read replicas, add connection pooling via PgBouncer.
- **Celery worker** — raise `max-instances`, keep `min-instances=1` (Celery Beat must be singleton — a second beat would cause duplicate email sends).
- **AI API costs** — the 1-hour ticker-level cache already amortizes well. At scale, extend TTL to 2-4 hours and add ticker-level rate limiting.
- **Email sending** — Gmail SMTP caps at ~500/day. At any real user count, migrate to SendGrid or AWS SES (~$0.10 per 1000 emails).
- **Redis** — Memorystore basic tier is fine for up to ~100K ops/sec. Switch to standard tier with HA for reliability at scale.

---

## Cost Analysis & Reduction Strategy

### Current production cost: ~$6-7/day (~$180-210/month)

| Service | Config | Daily cost |
|---|---|---|
| Celery worker | Cloud Run, `min-instances=1`, `cpu-throttling=false`, 1 vCPU, 512Mi | ~$2.00 (biggest driver) |
| Cloud SQL | db-f1-micro | ~$0.50 |
| Memorystore Redis | 1GB basic tier | ~$1.20 |
| VPC Connector | e2-micro | ~$0.15 |
| Backend API + Frontend | scale-to-zero | ~$0.10 |
| Secret Manager + Artifact Registry | free/tiny | ~$0 |

### Temporary pause (~$1.35/day)
```bash
bash deploy/pause_services.sh
```
Scales Cloud Run to zero, stops Cloud SQL. Memorystore and VPC connector remain (can't be paused, only deleted). Good for nights/weekends.

### Full destroy ($0/day)
```bash
bash deploy/destroy_all.sh
```
Deletes all GCP resources. Local Docker Compose still works for development. Best when the app doesn't need to be publicly accessible.

### Architectural optimizations (for long-term deployment)

If running this in production long-term, these would cut ~80% of the cost:

1. **Replace always-on Celery Beat with Cloud Scheduler + Cloud Run Jobs** (save ~$40/month). Cloud Scheduler pings an HTTP endpoint on cron; the backend enqueues or executes tasks. Worker scales to zero between invocations.
2. **Replace Memorystore with Upstash or a sidecar Redis** (save ~$35/month). Memorystore's minimum instance is overkill for our usage (a few hundred commands/hour). Upstash has a free tier covering 10k commands/day.
3. **Cloud SQL auto-pause** on newer tiers (db-perf-optimized-N-2) — not available on db-f1-micro, but would further cut the DB cost.
4. **Combine backend + worker into a single Cloud Run service** (save ~$30/month). Gunicorn and Celery in the same container halves Cloud Run cost. Loses some isolation, fine for low scale.
5. **Move to a single $5/month VPS** (save ~$170/month). For traffic under ~1000 users, a DigitalOcean droplet running Docker Compose would serve this just as well. Cloud Run's elasticity is overkill without viral growth.

### Pragmatic recommendation
- **Demo / portfolio**: current setup, pause when not in use.
- **Real product with <1k users**: collapse to a single VPS with Docker Compose (~$5-10/month).
- **Scaling product**: keep Cloud Run, apply optimizations 1 + 2.

---

## What's NOT in this project

Explicit non-goals — things we deliberately skipped and why:

- **Password reset flow** — not required by spec, and a tech interview demo doesn't benefit from it.
- **Social login (Google/GitHub OAuth)** — would conflict with the email verification model and doesn't add interview value.
- **Tests beyond Django's built-in checks** — the spec doesn't require them, and the time budget was spent on features/debugging.
- **Backwards-compatibility for old data** — the is_active field added mid-project uses `default=False`; existing rows in dev DB were updated manually. In production this would need a data migration.
- **Rate limiting at the API level** — DRF has throttling classes but not configured. For demo scale, not needed; for production, would add per-user and per-IP throttles.
- **Monitoring/alerting** — Cloud Run has built-in logs, but no Grafana/PagerDuty integration. Fine for a demo.

---

## Running and Deploying

See **[SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md)** for full setup and deployment instructions.
