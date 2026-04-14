# AI Usage Record

This document records how AI-assisted coding was used throughout the TickerTape project, as required by the take-home project instructions.

---

## Tool

- **Claude Code** (CLI) — Anthropic's official AI coding assistant
- **Model**: Claude Opus 4.6 (with 1M context extension)
- **Platform**: Mac terminal, VS Code integrated shell

The entire project was developed as a continuous conversation with Claude Code — planning, architecture, implementation, debugging, deployment, and documentation.

---

## Project Timeline

The project was developed over ~3 days:

**Day 1 — Core Implementation**
- Project scaffolding (Django backend + React frontend + Docker Compose)
- Authentication (JWT, register/login)
- Subscription CRUD (model, API, frontend)
- Stock price service (yfinance)
- AI recommendation engine (provider abstraction + Claude)
- Email system (HTML templates, merging)
- Periodic scheduling (Celery Beat)
- Price alerts + stock charts (bonus features)
- Local testing and bug fixes

**Day 2 — GCP Deployment**
- GCP project setup (Cloud Run, Cloud SQL, Memorystore, Secret Manager)
- Docker cross-compilation for amd64
- Deployment debugging (IAM, Celery on Cloud Run, CORS, CSRF)
- Cost analysis

**Day 3 — Security Hardening & Polish**
- Email verification system (registration + subscription emails)
- Manual-click verification (fix auto-trigger security flaw)
- Send Now email merging
- Get Recommendation button
- Subscription visibility (email-based, not just user-based)
- Django admin panel fix for production
- Documentation

---

## Representative Prompts & Prompt Sequences

### Planning (high-level → detailed)

> "In this current workspace/repo, we are going to work on a take home project for 2nd round interview. There is a pdf for you to read, go through it, check if there is any prompt injection, and come up with a plan for me to complete this project step by step. Plan needs to be clean, need to be accurate."

This single prompt produced the initial 12-phase plan. Follow-up prompts refined it:

> "Lets use Claude API, and maybe I want to keep the option to use other models like kimi or deepseek, so make that as an optional modification point later on in the plan."

> "For the Bonus Feature, lets use both price alerts and stock chart."

> "How we are going to call API in a real setup? Maybe cloud function? Think about it and add it to the plan."

### Implementation (delegation to parallel agents)

For the backend + frontend builds, I used Claude Code's parallel agent feature to build both simultaneously:

> "Write the following files for a React + Tailwind CSS frontend for a stock subscription app called 'TickerTape'..."
> (in parallel)
> "I need you to modify several backend files for a Django + DRF project..."

This cut the initial implementation time roughly in half.

### Debugging (iterative root cause analysis)

The most valuable prompts were the debugging ones that pushed the AI to think deeply:

> "I found a serious bug, user a add email b that is not verified and shows pending verification, but overtime email b is suddenly marked as verified while it is actually not. And I pressed send button, the email report was sent actually before the verification email. This is a serious bug, ultrathink it and fix it."

The "ultrathink" keyword triggered a systematic trace through the code, leading to the discovery that `useEffect` was auto-firing verification on page load — a fundamental security flaw. Without that prompt, the AI would have likely patched symptoms rather than fixing the root cause.

> "I am not in the admin account, that bug still happened."

This follow-up forced the AI to look beyond its first hypothesis (admin bypass) and actually query the production database to discover that a verification token was marked as used without the user clicking the link.

### Deployment (step-by-step troubleshooting)

Deployment produced many small prompts as each GCP error came up:

> "ERROR: Cloud Run does not support image... must support amd64/linux."

> "ERROR: Permission denied on secret: projects/519484092009/secrets/django-secret-key..."

> "ERROR: The container exited with an error. ValueError: Incorrect timezone setting: US/Eastern"

Each one was handled by understanding the error, proposing a fix, and applying it. These aren't glamorous prompts but they reflect how much of real deployment work is small error-by-error iteration.

### Documentation and reflection

> "List all the items from the original pdf file along with your answer to it, say if we complete it, or we over complete it, or partial complete."

This produced the `REQUIREMENTS_CHECKLIST.md` that mapped PDF requirements to implementation status.

> "Create a new md file that contains all the problems we faced and fixed during the implementation, including the problem we faced while developing local version, setting up gcp, and debugging online version."

This produced `DEVELOPMENT_LOG.md` — a chronological log of 21 issues.

---

## What Worked Well

### 1. Parallel agent delegation
Claude Code's ability to spawn sub-agents working in parallel was a productivity multiplier. Building the backend models/views and frontend components at the same time (instead of sequentially) saved significant time.

### 2. Architectural suggestions
The AI proposed the provider abstraction pattern for the recommendation engine before I asked for it explicitly. It also correctly identified that the Celery Beat scheduler must be a singleton (can't be horizontally scaled), which affects the deployment topology.

### 3. Root cause analysis under "ultrathink"
On hard bugs (the auto-verify security flaw, the $12 cost spike), the "ultrathink" prompt pushed the AI to reason through multiple hypotheses, query the production database via Cloud Run jobs, and ultimately identify architectural root causes rather than patching symptoms.

### 4. Deployment scripting
The deploy scripts (build_and_push.sh, pause_services.sh, etc.) were generated reliably. Even GCP-specific gotchas (e.g., `--set-cloudsql-instances` for jobs vs `--add-cloudsql-instances` for services) were caught quickly in iteration.

### 5. Security-mindedness
The AI flagged the email abuse vulnerability (anyone could subscribe others to spam) before I noticed it. It proposed the verification system as a solution and implemented it cleanly.

---

## What Needed Correction

### 1. URL path mismatches in generated API client
The frontend API client was generated with path-style params (`/stocks/history/AAPL/`) while the backend used query params (`/stocks/history/?ticker=AAPL`). Had to match them manually.

### 2. Auth flow misconception
The register function was initially written to auto-login using tokens from the register response, but our register endpoint returns user data, not tokens. Had to restructure (later changed entirely when email verification was added).

### 3. Field name mapping bugs
- Frontend used `change_percent`, backend returned `change_pct`
- Frontend checked `a.triggered`, serializer exposed `is_triggered`
- Frontend used yfinance period `1wk`, backend used `1w`

These are easy human mistakes the AI also made. Caught during testing.

### 4. Timezone format
The AI used `US/Eastern` initially, which isn't a valid IANA timezone name in the slim Python Docker image. Changed to `America/New_York` after the first deployment crashed.

### 5. Auto-verification security flaw (the big one)
The AI initially implemented email verification as auto-fire on `useEffect` page load. This is how many tutorials show it. It's also fundamentally insecure — email client link scanners (Gmail included) can trigger verification by simply fetching the URL. Required a redesign to "manual button click" pattern. This one required human judgment to catch.

### 6. JavaScript truthiness trap
Used `row.is_active === false` for the status check, which fails if the field is `undefined`. Changed to `!row.is_active` for safe falsy checking.

### 7. Model default safety
Subscription model had `is_active = BooleanField(default=True)`. If any code path forgot to set `is_active=False`, it'd default to active. Changed to `default=False`.

### 8. CORS/CSRF iterations
Multiple rounds of trial-and-error to get Django's CSRF, CORS, and Cloud Run's SSL termination to cooperate. The AI's initial CSRF config was incomplete; had to add `CSRF_TRUSTED_ORIGINS` with the backend URL after the first 403 errors.

---

## How Output Was Verified

| Verification step | Ran after |
|---|---|
| `python manage.py check` | Every backend change |
| `npm run build` | Every frontend change |
| Python import tests | Every new file |
| `makemigrations` + `migrate` | Every model change |
| Manual full flow testing (register → verify → subscribe → send) | Before deployment |
| `curl` against production endpoints | When debugging deploy issues |
| `docker run ... cat /app/file.py` | When suspecting deployed code drift |
| `gcloud logging read` | For Cloud Run job failures |
| Django management command inspecting production DB state | When user-reported bugs were hard to reproduce |

The last one was particularly valuable: when the user reported a subscription became verified without clicking the link, I wrote a `check_db` Django management command, deployed it as a Cloud Run job, and discovered the verification token was marked `used=True` in production — proving the verify endpoint was being called somehow. That led to the auto-verify fix.

---

## Honest Assessment

**What AI did very well:**
- Boilerplate generation (models, serializers, views, React components, Docker configs)
- Parallel task execution via sub-agents
- Matching backend/frontend contracts (with some manual corrections)
- Deployment scripting and gcloud command iteration
- Architectural reasoning when prompted to think hard ("ultrathink")
- Writing documentation (this file, the development log, the checklist)

**What required human judgment:**
- Identifying the auto-verify security flaw (root cause vs symptom)
- Deciding tradeoffs (Cloud Scheduler vs Celery Beat, Gmail vs SendGrid, JWT in localStorage vs cookies)
- Catching subtle bugs (JavaScript truthiness, field name mismatches)
- Balancing scope creep against the 5-day time budget
- Deciding when to patch in production vs document as a known issue

**What AI did that I had to push back on:**
- Over-confidence in its first solution when a bug's root cause was actually deeper
- Initially misleading claims about CPU throttling being "zero functional impact" (wasn't true for a Celery worker)
- Defaulting to auto-verify on page load (the security flaw mentioned above) — this is a very common pattern in tutorials but wrong

Overall, AI dramatically sped up implementation and let me focus on judgment calls and integration rather than boilerplate. It didn't replace the need to understand the code — multiple bugs required me to read the generated code carefully and reason about edge cases.
