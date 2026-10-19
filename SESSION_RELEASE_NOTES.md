# Garmin session patch — 19 October 2026

Fixes the incompatible old Garth OAuth files (`oauth1_token.json`, `oauth2_token.json`) and `client.garth.dump` path. GarminConnect 0.3.19 uses `Garmin.client.dumps()` / `Garmin.login(tokenstore=JSON)`. Stored JSON is encrypted with Fernet in `public.paceflow_garmin_sessions` and isolated by athlete UUID. Restored sessions are opened without username/password to prevent an automatic credential fallback. Refreshed tokens are persisted after successful login.

## Prerequisites
- Existing table `public.paceflow_garmin_sessions` (confirmed created by operator)
- Render environment: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GARMIN_SESSION_FERNET_KEY` (Fernet key; do not paste into chat). Keep key stable across deployments.
- If the encryption key is rotated, old sessions must be re-encrypted or deliberately reauthorized.
- Existing Garmin rate-limit 429/403 is not bypassed. Because the table currently has zero sessions, the first connection still needs Garmin to accept a credential login.
- Verify ledger state and Garmin Connect before any retry of a previously uncertain workout.

## Checks performed
- Python compilation and three mocked session-flow tests passed.
- Not tested against Garmin network, actual Render environment, or live Supabase.
- Not a proof of end-to-end delivery; stage first.
