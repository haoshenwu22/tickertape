# TickerTape

A web app for subscribing to stock price updates by email, with AI-generated Buy/Hold/Sell recommendations.

Built for the Hextom Software Engineer 2nd Round Take-Home Project.

**Live Demo:** https://tickertape-web-519484092009.us-central1.run.app
**Admin Panel:** https://tickertape-api-519484092009.us-central1.run.app/admin/

## Documents

| File | Purpose |
|---|---|
| `README.md` | Design notes, assumptions, tradeoffs (this file) |
| `SETUP_INSTRUCTIONS.md` | How to run locally / deploy to GCP |
| `AI_USAGE.md` | How AI was used in this project |
| `REQUIREMENTS_CHECKLIST.md` | PDF requirements → implementation status |
| `DEVELOPMENT_LOG.md` | Chronological bug log (22 issues encountered) |

## Features

Stock subscriptions with ticker validation (yfinance) · AI Buy/Hold/Sell recommendations (Claude, with provider abstraction) · Blocking email verification on registration and subscription emails · Email merging (periodic + Send Now) · Hourly Mon-Fri 9-5 ET scheduling (Celery Beat) · Price alerts (bonus) · Interactive stock charts (bonus) · Admin/regular user roles · Django admin panel

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Django 6, DRF |
| Frontend | React 18, Vite, Tailwind CSS 4 |
| Database | PostgreSQL 16 |
| Tasks | Celery + Redis (django-celery-beat) |
| Stock Data | yfinance |
| AI | Claude API (Haiku) with provider abstraction |
| Email | Gmail SMTP (async via Celery) |
| Auth | JWT (simplejwt) + email verification |
| Deployment | GCP Cloud Run + Cloud SQL + Memorystore + Secret Manager |

## Architecture

```
┌─────────────┐     ┌───────────────────────┐     ┌───────────┐
│  React SPA  │────▶│  Django REST API      │────▶│PostgreSQL │
└─────────────┘     │  - Auth (JWT) + Verify│     └───────────┘
  Cloud Run         │  - Subscriptions CRUD │
                    │  - Stock/AI/Email     │────▶ yfinance + Claude + Gmail
                    └──────────┬────────────┘
                     Cloud Run │
                    ┌──────────▼────────────┐     ┌───────────┐
                    │  Celery Worker + Beat │────▶│   Redis   │
                    │  - Periodic emails    │     └───────────┘
                    │  - Price alert checks │
                    └───────────────────────┘
                      Cloud Run
```

## Key Assumptions

1. **Subscription email need not be the subscriber's own email.** Users can enter any email, but unverified addresses trigger a verification flow before activation (prevents spam abuse).
2. **"Merge emails" applies to Send Now too, not just periodic.** Clicking Send Now on any subscription sends one merged email for all active subscriptions at that address.
3. **No market-holiday awareness.** Schedule is strictly Mon-Fri 9-5 ET regardless of trading calendar.
4. **Admins are trusted.** `is_staff=True` bypasses all email verification.
5. **AI recommendations are cached per ticker, not per user.** Two users on AAPL get identical text within a 1-hour TTL — avoids duplicate Claude API calls.
6. **Modest scale.** Designed for ~hundreds of users. At 10x-100x, Gmail, Memorystore tier, and Celery Beat singleton would need replacement.

## Important Decisions

**AI provider abstraction** — `RecommendationProvider` base class lets us swap Claude for DeepSeek/Kimi/rule-based in one new file. Also gives us a built-in fallback when the API fails.

**Blocking email verification on registration** — account is inactive until verified. Standard modern UX; without it anyone can spam others' inboxes. Verification emails send async via Celery so the API response stays fast.

**Verification requires manual button click, not auto-fire on page load.** Initially implemented as auto-verify in `useEffect`; discovered (via production DB inspection) that email client link scanners were triggering verification before users even saw the email. Rewrote to require explicit click.

**Celery worker is always-on (`min-instances=1`, 1Gi memory).** Celery Beat must run 24/7 to fire scheduled jobs on time. 1Gi is needed — we initially used 512Mi and saw OOM crashes causing delayed and duplicate emails. Biggest single cost (~$2.50/day).

**`Subscription.is_active` defaults to `False`.** Fail-safe: any code path that forgets to set the flag creates a pending (inactive) subscription, not an accidentally-active one.

**Subscription visibility is email-based, not just user-based.** Users see subscriptions where `user=me` OR `email IN my_verified_emails`, so they can manage/delete unwanted subscriptions targeting their address.

**Frontend calls the backend directly (no Nginx proxy).** Attempted an Nginx proxy first; hit 502s due to Cloud Run's SSL termination. Direct calls with CORS + `VITE_API_URL` baked in at build time are simpler.

**JWT in localStorage, not HttpOnly cookies.** Simpler for this demo; accepts XSS risk in exchange for less complexity. For real production with sensitive data, switch to HttpOnly refresh cookie + short-lived access token in memory.

## Scaling Notes

- **Backend API** auto-scales on Cloud Run; raise `max-instances` beyond current 3.
- **Cloud SQL** upgrade from db-f1-micro, add connection pooling (PgBouncer) and read replicas.
- **Celery worker** horizontal scale OK; `min-instances=1` stays (Beat must be singleton).
- **Gmail SMTP** caps at ~500/day — swap to SendGrid/SES at any real scale.
- **AI costs** — 1-hour ticker-level cache amortizes well; extend TTL or add rate limits if needed.

## Cost & Shutdown

Current production cost: ~$7/day. Biggest driver is the always-on Celery worker (~$2.50/day).

To reduce: `bash deploy/pause_services.sh` (~$1.35/day floor — Memorystore and VPC connector can't be paused) or `bash deploy/destroy_all.sh` ($0/day, local Docker Compose still works).

Long-term optimizations (Cloud Scheduler instead of always-on Beat, Upstash instead of Memorystore, or collapsing to a $5 VPS) could cut ~80% of cost. See `DEVELOPMENT_LOG.md` for the OOM debugging story.

## Setup

See **[SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md)**.
