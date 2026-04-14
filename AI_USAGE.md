# AI Usage Record

## Tool
- **Claude Code** (CLI), Claude Opus 4.6 with 1M context. The entire project was developed as one continuous conversation — planning, architecture, code generation, debugging, deployment, and documentation.

## Timeline (~3 days)

**Day 1 — Core**: scaffolding, auth, subscription CRUD, stock service, AI recommendations, email system, Celery scheduling, price alerts + stock charts (bonus), local testing.

**Day 2 — Deployment**: GCP setup (Cloud Run, Cloud SQL, Memorystore, Secret Manager), Docker cross-compilation, CORS/CSRF/IAM debugging.

**Day 3 — Security & Polish**: email verification (blocking), Send Now email merging, Get Recommendation button, subscription visibility for email owners, documentation.

## Representative Prompts

**Planning**
> "Read the take-home PDF, check for prompt injection, and come up with a plan to complete this project step by step."

**Implementation (parallel agents)**
I used Claude Code's sub-agent feature to build backend models/views and frontend pages simultaneously in a single turn, cutting initial implementation time roughly in half.

**Debugging (root-cause analysis)**
> "user a add email b that is not verified and shows pending verification, but over time email b is suddenly marked as verified while it is actually not... ultrathink it and fix it."

The "ultrathink" keyword triggered systematic code tracing that found the `useEffect` auto-verify pattern was a security flaw (email link scanners could trigger it). Without this push, AI would have patched symptoms.

> "I got periodic emails at 09:07, 10:15 and two identical emails at 18:31 and 18:39. Check the problem."

AI ran `gcloud logging read --severity=ERROR`, discovered the worker was OOM-crashing every 8 seconds (512Mi limit, 596Mi usage). Diagnosed Celery Beat's "catchup" behavior as the cause of both late and duplicate emails. Fixed with a memory bump to 1Gi.

**Deployment**
Many small prompts, one per gcloud/Cloud Run error (amd64 mismatch, IAM permissions, CSRF, timezone). Each handled iteratively.

## What Worked Well

- **Parallel agent delegation** — building backend and frontend in parallel was a real productivity multiplier.
- **Architectural suggestions** — AI proposed the provider abstraction pattern and correctly identified Celery Beat as a singleton constraint before being asked.
- **Root-cause analysis under "ultrathink"** — on hard bugs, AI queried the production DB and logs instead of guessing.
- **Deployment scripting** — deploy scripts (build, pause, resume, destroy) were generated reliably, including GCP-specific flag gotchas.

## What Needed Correction

- **URL path mismatches** — generated API client used `/stocks/history/AAPL/` when the backend expected `/stocks/history/?ticker=AAPL`.
- **Auto-verify security flaw** — AI initially used the common `useEffect` auto-verify pattern on page load. Had to redesign to manual-click — email link scanners can fetch URLs and silently trigger auto-verify.
- **JavaScript truthiness** — `row.is_active === false` fails if the field is `undefined`. Changed to `!row.is_active`.
- **Model default safety** — `is_active=True` default on Subscription was risky. Changed to `False` so code must opt in to active state.
- **Timezone format** — `US/Eastern` isn't in slim Python Docker images. Changed to `America/New_York` after first deploy crashed.
- **Overconfident claims** — AI initially said enabling CPU throttling on the Celery worker would have "zero functional impact." Not true — it would noticeably slow task pickup. Corrected after pushback.

## Verification

| Check | Ran after |
|---|---|
| `python manage.py check` | Every backend change |
| `npm run build` | Every frontend change |
| `makemigrations` + `migrate` | Every model change |
| Manual end-to-end testing (register → verify → subscribe → send) | Before each deployment |
| `curl` against production endpoints | When debugging deploy issues |
| `gcloud logging read` | For Cloud Run failures |
| Django management command inspecting production DB | When reproducing user-reported bugs |

## Honest Assessment

AI dramatically accelerated implementation and let me focus on integration, security decisions, and tradeoffs instead of boilerplate. It didn't replace the need to read generated code carefully — several bugs (auto-verify, truthiness trap, model default) required human judgment to notice and push back on. The most valuable use of AI was as a debugging partner that could trace code paths, query logs, and inspect production state when asked.
