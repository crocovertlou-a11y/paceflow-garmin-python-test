# PaceFlow Garmin — integrated feature-branch candidate

Source: user-supplied ZIP `paceflow-garmin-python-test-feature-garmin-session-persistence.zip`.

## Verified offline
- Original existing test suite: 32 passed.
- Combined suite including session CAS and API integration: 39 passed.
- `compileall` succeeded.
- Real `api.py` now uses `garmin_session_runtime.login` in both `/workouts/send` and `/activities/candidates`.
- Both request models accept omitted Garmin password. Feature is **off** unless `PACEFLOW_GARMIN_SESSION_MODE=enabled`.
- Confirmed sends remain marked sent even if token persistence subsequently fails.
- Service-side ownership checks and existing idempotency claim/finish remain.

## IMPORTANT: NOT YET PRODUCTION READY
1. Supabase SQL `SQL_GARMIN_SESSIONS_MIGRATION_REVIEW.sql` is **review-only**. Check actual athlete_profiles FK, schema, grants, and deployment policy before applying.
2. The current front-end / Netlify bridge has not been modified; it may still require email and password on every request. End-to-end passwordless UX is not yet validated.
3. Concurrent session writes are protected by compare-and-swap. On conflict the service fails closed before upload or keeps a confirmed send; no token overwrite. A follow-up UX for reconnect/conflict remains necessary.
4. Live Garmin MFA, expired token recovery, 429 responses, and a staging environment test are not yet validated.
5. Session refresh persistence occurs after Garmin API operations; a failed refresh save can require reconnect. No secret should appear in logs.
6. Pinning `garminconnect==0.3.19` may change installed Render version. Confirm compatibility on staging before deploy.

## Required server secrets (when enabled)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (already used by ledger)
- `PACEFLOW_GARMIN_SESSION_FERNET_KEY`: generate using `cryptography.fernet.Fernet.generate_key()`; never commit.
- `PACEFLOW_GARMIN_SESSION_MODE=enabled` only after staging validation.

Do NOT overwrite `main` or deploy to Render production from this archive yet.
