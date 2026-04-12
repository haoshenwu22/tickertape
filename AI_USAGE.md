# AI Usage Record

This document records how AI-assisted coding was used throughout this project, as required by the take-home project instructions.

## AI Tool Used
- **Claude Code** (CLI) — Anthropic's official AI coding assistant
- Model: Claude Opus 4.6

## Project Plan / Task Breakdown

The project was planned in a structured conversation with Claude Code:

1. **Phase 1:** Project scaffolding (Django + React + Docker)
2. **Phase 2:** Authentication system (JWT, login/register)
3. **Phase 3:** Subscription CRUD (model, API, frontend)
4. **Phase 4:** Stock price service (yfinance integration)
5. **Phase 5:** AI recommendation engine (provider abstraction)
6. **Phase 6:** Email system (templates, merge logic)
7. **Phase 7:** Periodic scheduling (Celery Beat)
8. **Phase 8:** Price alerts (bonus feature)
9. **Phase 9:** Stock charts (bonus feature)
10. **Phase 10:** Polish and testing
11. **Phase 11:** Documentation
12. **Phase 12:** GCP deployment

## Representative Prompts

### Planning
- "Read the take-home PDF and come up with a plan to complete this project step by step"
- Discussion of tech stack trade-offs (AI provider choice, deployment platform, email service)
- Decision-making on bonus features (price alerts + stock charts)

### Implementation
- "Build the Django backend with models, serializers, views for all apps"
- "Create the React frontend with auth context, API service, and all pages"
- "Write the AI recommendation engine with provider abstraction for future model swaps"

### Review
- "Verify all backend imports work correctly"
- "Build the frontend and check for compilation errors"
- "Run Django system checks"

## What Worked Well

1. **Parallel implementation** — Claude Code's agent system allowed building backend and frontend components simultaneously
2. **Architecture decisions** — The AI provider abstraction pattern was suggested by Claude and cleanly separates concerns
3. **Boilerplate generation** — Django models, serializers, views, and React components were generated quickly and correctly
4. **API consistency** — Frontend API client was generated to match backend URL patterns, with corrections made where they diverged

## What Needed Correction

1. **URL path mismatches** — The generated frontend API client used path-style params (`/stocks/history/AAPL/`) instead of query params (`/stocks/history/?ticker=AAPL`) that the backend expects. Fixed manually.
2. **Auth flow** — The register function initially tried to extract JWT tokens from the register response, but our backend returns user data on registration, not tokens. Fixed to auto-login after registration.
3. **Field name mapping** — Frontend dashboard referenced `change_percent` instead of `change_pct` from the backend response. Fixed to match actual API response shape.
4. **Period value format** — Frontend used yfinance period format (`1wk`) instead of our backend's simplified format (`1w`). Fixed to match.

## How Output Was Verified

1. **Django system checks** — `python manage.py check` returned 0 issues
2. **Import verification** — All backend modules imported successfully
3. **Frontend build** — `npm run build` compiled with 0 errors
4. **Migration generation** — `python manage.py makemigrations` created all 3 migrations correctly
5. **Manual testing** — (to be completed during local development with Docker Compose)
