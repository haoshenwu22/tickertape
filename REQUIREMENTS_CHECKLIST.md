# Requirements Checklist

Mapping each requirement from the take-home project PDF to our implementation.

---

### 1. Web-based UI for creating subscriptions
> The user inputs a stock ticker (e.g. "AAPL") and an email address. Both should be validated: the ticker must refer to a real stock symbol, the email must be in valid format.

**Status: OVER-COMPLETE**

- Ticker validation via `yfinance.Ticker(symbol).info` — rejects invalid symbols with clear error message
- Email format validation via Django's EmailValidator
- Added beyond requirements: email ownership verification (verification email sent for unverified addresses), subscription status tracking (active/pending), email pre-filled with user's registered email

---

### 2. Web-based UI for viewing subscriptions
> Each entry shows the stock ticker, current price, and email address, with a "Delete" button and a "Send Now" button. Send Now emails the current price with AI recommendation to the subscriber.

**Status: OVER-COMPLETE**

- Table shows: Ticker, Company Name, Current Price, Change%, 7-day Sparkline Chart, AI Recommendation, Email, Status, Actions
- Delete button with instant removal
- Send Now button (disabled for pending/unverified subscriptions)
- Added beyond requirements: "Get Rec." button for on-demand AI recommendations per row, subscription status badges (Active/Pending verification), admin view showing all subscriptions

---

### 3. Periodic sending: every hour, Monday-Friday, 9 AM-5 PM Eastern Time
> Some scheduling details are intentionally left for you to decide and document.

**Status: COMPLETE**

- Celery Beat schedule: `crontab(minute=0, hour='9-17', day_of_week='1-5')` in `America/New_York` timezone
- 9 sends per day max (9:00, 10:00, ..., 17:00 ET)
- Only sends to active (verified) subscriptions
- Skips if no active subscriptions exist
- Documented decision: no market holiday awareness (deliberate simplification)
- Celery worker runs as always-on Cloud Run service (`min-instances=1`)

---

### 4. Merge emails when possible
> If user@example.com subscribes to AAPL and BB, send one email with both prices instead of two.

**Status: OVER-COMPLETE**

- Periodic emails: groups all active subscriptions by email address, sends one merged email per unique email
- Send Now: also merges — clicking Send Now on any subscription sends a merged email containing ALL active subscriptions for that email address (not just the one clicked)
- The original version only merged for periodic emails; we enhanced Send Now to merge as well after identifying this gap

---

### 5. Use Yahoo Finance for stock price data
> yfinance library is acceptable. A mock fallback is fine if the API is unavailable.

**Status: COMPLETE**

- Primary: `yfinance` library for real-time prices and historical data
- Batch fetching via `yfinance.Tickers()` for efficiency
- Mock fallback with hardcoded prices for 5 popular stocks (AAPL, GOOGL, MSFT, AMZN, TSLA) when yfinance is unavailable
- Mock data flagged with `is_mock: true` in API response

---

### 6. Secure login system
> Regular users see only their own subscriptions. Admins see all subscriptions across all users.

**Status: OVER-COMPLETE**

- JWT authentication (access: 30min, refresh: 7 days) via djangorestframework-simplejwt
- Blocking email verification on registration (account inactive until email verified)
- Regular users see: their own subscriptions + subscriptions from other users targeting their verified emails
- Admin users (`is_staff=True`) see all subscriptions across all users
- Admin badge displayed in the UI header
- Added beyond requirements: email verification for subscription emails, protection against email abuse, Django admin panel for database management

---

### 7. AI-generated Buy/Hold/Sell recommendation per stock
> A lightweight approach is fine if clearly explained.

**Status: OVER-COMPLETE**

- Claude API (Haiku model) generates natural-language recommendations with reasoning
- Provider abstraction pattern: easily swap to DeepSeek, Kimi, or any other model by implementing one Python class
- Rule-based fallback if AI provider fails (>3% up = Sell, >3% down = Buy, else Hold)
- Recommendations cached in Redis for 1 hour per ticker to reduce API costs
- Added beyond requirements: on-demand "Get Rec." button in the dashboard UI (not just in emails), recommendation reason displayed as tooltip text

---

### 8. One feature of your choice that meaningfully enhances this product
> Explain what you built, why you chose it, and what value it adds.

**Status: OVER-COMPLETE (two features instead of one)**

**Feature 1: Price Alerts**
- Users set target price + condition (above/below)
- Celery task checks every 15 minutes
- Email notification sent when condition is met
- One-time trigger (alert marked as triggered, won't fire again)
- Value: immediate actionable notifications vs. waiting for hourly digest

**Feature 2: Stock Charts**
- 7-day sparkline previews in the subscription table
- Clickable sparkline opens full interactive chart modal
- Period selector: 1W, 1M, 3M, 1Y
- Color-coded: green trending up, red trending down
- Recharts with responsive design and hover tooltips
- Value: visual context for price movements without leaving the app

---

### 9. Python + Django + PostgreSQL backend, React + Tailwind CSS frontend

**Status: COMPLETE**

- Backend: Python 3.12, Django 6, Django REST Framework, PostgreSQL 16
- Frontend: React 18 (Vite), Tailwind CSS 4
- All requirements met exactly as specified

---

### 10. Use AI-assisted coding as much as possible
> We are evaluating how effectively you use AI as an engineering tool.

**Status: COMPLETE**

- Used Claude Code (CLI) with Claude Opus 4.6 throughout the entire project
- AI used for: planning, architecture decisions, code generation, debugging, deployment scripting
- Human corrections applied for: URL mismatches, auth flow logic, security vulnerabilities, deployment configurations
- Full record in `AI_USAGE.md`

---

### 11. Submit source code link and hosted/working product
> No later than 5 business days after receiving this document.

**Status: COMPLETE**

- Source: GitHub repository
- Live: https://tickertape-web-519484092009.us-central1.run.app
- Deployed on GCP Cloud Run with Cloud SQL, Memorystore Redis, and Secret Manager

---

### 12. Brief record of AI usage
> Project plan/task breakdown, representative prompts, what worked well, what needed correction, and how you verified output.

**Status: OVER-COMPLETE**

- `AI_USAGE.md` — structured AI usage record with prompts, corrections, verification methods
- `DEVELOPMENT_LOG.md` — detailed log of 21 problems encountered and solved during development
- `REQUIREMENTS_CHECKLIST.md` — this document mapping requirements to implementation

---

## Summary

| Req# | Description | Status |
|------|-------------|--------|
| 1 | Subscription creation UI with validation | Over-complete |
| 2 | Subscription viewing UI with Delete/Send Now | Over-complete |
| 3 | Periodic hourly sending Mon-Fri 9-5 ET | Complete |
| 4 | Merge emails for same address | Over-complete |
| 5 | Yahoo Finance with mock fallback | Complete |
| 6 | Secure login with user/admin roles | Over-complete |
| 7 | AI Buy/Hold/Sell recommendations | Over-complete |
| 8 | One bonus feature | Over-complete (two features) |
| 9 | Django + PostgreSQL + React + Tailwind | Complete |
| 10 | AI-assisted coding | Complete |
| 11 | Source code + hosted product | Complete |
| 12 | AI usage record | Over-complete |
