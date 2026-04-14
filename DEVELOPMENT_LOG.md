# Development Log: Problems Encountered and Solutions

This document records all significant problems encountered during development, deployment, and testing of the TickerTape project, along with how each was resolved.

---

## Phase 1: Local Development

### 1. Login error message disappears instantly
**Problem:** When a user entered wrong credentials (e.g., email instead of username), the error message appeared for less than 1 second then vanished.

**Root cause:** The Axios response interceptor caught the 401 from the login endpoint, attempted a token refresh (which also failed), then cleared localStorage and did `window.location.href = "/login"` — a full page reload that wiped the React error state.

**Fix:** Excluded `/auth/login/` and `/auth/register/` URLs from the 401 interceptor logic so login errors are handled by the component, not the interceptor.

### 2. Stock chart tooltip lag
**Problem:** Moving the mouse quickly over the stock chart showed the tooltip lagging behind the cursor.

**Root cause:** Recharts default tooltip animation.

**Fix:** Disabled tooltip animation: `isAnimationActive={false}` and `animationDuration={0}` on the Tooltip component.

### 3. Generic duplicate subscription error
**Problem:** Adding a subscription that already existed showed "Failed to add subscription" instead of a helpful message.

**Root cause:** Django's IntegrityError from the unique constraint wasn't being caught — it returned a generic 500.

**Fix:** Wrapped `serializer.save()` in a try/except for IntegrityError, returning a clear message: "You already have a subscription for {ticker} with this email address."

### 4. Price alerts stuck as "Active" on dashboard
**Problem:** After triggering price alerts via the Django shell, the dashboard still showed them as "Active" instead of "Triggered."

**Root cause:** Two issues: (a) The frontend checked `a.triggered` but the API serializer returned the field as `is_triggered`. (b) The dashboard didn't auto-refresh alert data.

**Fix:** Fixed the field name to `a.is_triggered` and added a 30-second auto-refresh interval for the alerts tab.

### 5. "Rec." column always shows "--"
**Problem:** The Recommendation column in the subscription table always displayed "--" with no way to get recommendations without sending an email.

**Root cause:** Recommendations were only generated during Send Now/periodic emails, never displayed in the UI.

**Fix:** Added a "Get Rec." button per row that calls a new `/api/stocks/recommendation/` endpoint, fetches the AI recommendation on demand, and displays the Buy/Hold/Sell badge with the reasoning text.

---

## Phase 2: GCP Deployment

### 6. Docker image architecture mismatch
**Problem:** `Cloud Run does not support image... must support amd64/linux`

**Root cause:** Docker on Apple Silicon (M-series Mac) builds ARM images by default, but Cloud Run runs on x86/amd64.

**Fix:** Added `--platform linux/amd64` flag to all `docker build` commands.

### 7. Secret Manager permission denied
**Problem:** Cloud Run deployment failed with "Permission denied on secret" for all 6 secrets.

**Root cause:** The Cloud Run default service account didn't have the Secret Manager Secret Accessor role.

**Fix:** Granted the role: `gcloud projects add-iam-policy-binding ... --role=roles/secretmanager.secretAccessor`

### 8. Celery worker fails to start on Cloud Run
**Problem:** The Celery worker Cloud Run service failed with "container failed to start and listen on port."

**Root cause:** Cloud Run expects every service to listen on an HTTP port. Celery is a background worker that doesn't serve HTTP.

**Fix:** Created `worker_entrypoint.sh` that starts a minimal Python HTTP health-check server on port 8080 in the background, then starts the Celery worker.

### 9. Invalid timezone "US/Eastern"
**Problem:** Migration job crashed with `ValueError: Incorrect timezone setting: US/Eastern`

**Root cause:** The slim Python Docker image doesn't include the `US/Eastern` timezone alias. Only IANA timezone names work.

**Fix:** Changed `TIME_ZONE` and `CELERY_TIMEZONE` from `US/Eastern` to `America/New_York`.

### 10. Frontend Nginx proxy 502 Bad Gateway
**Problem:** The frontend's Nginx proxy to the backend returned 502 for all API requests.

**Root cause:** Nginx inside Cloud Run couldn't resolve/reach the backend Cloud Run service URL. Cloud Run services communicate over the public internet, and Nginx's proxy_pass configuration had issues with SSL and host headers.

**Fix:** Removed the Nginx proxy entirely. Changed the React app to call the backend API directly using `VITE_API_URL` environment variable baked in at build time. Simplified nginx.conf to only serve static files with SPA fallback.

### 11. Django Admin 500 error in production
**Problem:** Visiting `/admin/` returned "Server Error (500)."

**Root cause:** Django admin needs static files (CSS/JS) collected and served. The Docker image didn't run `collectstatic`.

**Fix:** Added `RUN python manage.py collectstatic --noinput` to Dockerfile.backend, with WhiteNoise middleware serving the files.

### 12. Django Admin CSRF 403 error
**Problem:** Logging into the Django admin panel returned "Forbidden (403) CSRF verification failed."

**Root cause:** Cloud Run terminates SSL at the load balancer and forwards HTTP to the container. Django's CSRF middleware didn't trust the origin because `CSRF_TRUSTED_ORIGINS` wasn't configured.

**Fix:** Added `CSRF_TRUSTED_ORIGINS` setting and set it to the backend's Cloud Run URL via environment variable.

### 13. gcloud command pasting issues
**Problem:** Multi-line gcloud commands with backslash continuations broke when pasted into the terminal due to trailing whitespace.

**Root cause:** Extra spaces before backslashes in formatted code blocks.

**Fix:** Saved long commands to `.sh` scripts and ran them with `bash script.sh` instead of pasting directly.

### 14. Cloud Run job flag mismatch
**Problem:** Migration Cloud Run job failed with "unrecognized arguments: --add-cloudsql-instances."

**Root cause:** Cloud Run Jobs use `--set-cloudsql-instances` while Cloud Run Services use `--add-cloudsql-instances`.

**Fix:** Changed the flag to `--set-cloudsql-instances` for job commands.

---

## Phase 3: Email Verification & Security

### 15. Email abuse vulnerability
**Problem:** Any logged-in user could subscribe any email address and spam "Send Now" to send unwanted emails to that address. The email owner had no way to manage or delete these subscriptions.

**Root cause:** No email ownership verification, and subscriptions were only visible to the user who created them.

**Fix (multi-part):**
- Added blocking email verification on registration (account inactive until verified)
- Subscriptions to unverified emails are created as "pending" (is_active=False) and require email verification
- Admin users bypass verification
- Users can now see and delete subscriptions targeting their verified email addresses (not just ones they created)

### 16. Auto-verification security flaw
**Problem:** Email verification happened automatically when the verification page loaded, which meant email client link scanners, browser prefetchers, and React's double-render in development mode could trigger verification without the user's explicit action.

**Root cause:** The VerifyEmailPage used a `useEffect` that immediately called the verify API on mount.

**Fix:** Replaced auto-verify with a manual "Verify Email" button that requires explicit user click. The page loads but does NOT call the API until the button is pressed.

### 17. Verification token double-fire
**Problem:** React's useEffect fired twice, causing the first verify call to succeed and the second to fail with "token already used," showing the user an error even though verification succeeded.

**Root cause:** React Strict Mode (development) or component remount causing double execution of useEffect.

**Fix:** (Addressed by fix #16) Manual button click prevents double-fire entirely. Also added handling: if "already been used" error is received, show success instead of error.

### 18. Slow verification emails blocking API response
**Problem:** Registration and subscription creation took 5-15 seconds because the API waited for Gmail SMTP to send the verification email before returning.

**Root cause:** `send_mail()` was called synchronously during the API request.

**Fix:** Moved email sending to an async Celery task (`send_verification_email_task.delay()`). The API responds immediately (~50ms), and the email is sent in the background by the Celery worker.

### 19. Subscription status display bug
**Problem:** Pending subscriptions sometimes showed as "Active" on the dashboard.

**Root cause:** The status check used `row.is_active === false` in JavaScript. If `is_active` was `undefined` (e.g., field missing from response), `undefined === false` evaluates to `false`, falling through to show "Active."

**Fix:** Inverted the logic to `row.is_active ? "Active" : "Pending verification"` — now anything that isn't explicitly `true` shows as pending.

### 20. Subscription model default was is_active=True
**Problem:** If any code path created a subscription without explicitly setting `is_active=False`, it would default to active, bypassing verification.

**Root cause:** The model field was defined as `is_active = BooleanField(default=True)`.

**Fix:** Changed default to `False`. All code paths that should create active subscriptions (admin, verified emails) explicitly pass `is_active=True`.

### 21. Admin subscriptions invisible to target user
**Problem:** When an admin created a subscription targeting user A's email, user A couldn't see it on their dashboard.

**Root cause:** The subscription list query only filtered by `user=request.user`, so users only saw subscriptions they personally created.

**Fix:** Updated the query to show subscriptions where `user=me` OR `email IN my_verified_emails`. Same logic applied to delete and Send Now permissions.
