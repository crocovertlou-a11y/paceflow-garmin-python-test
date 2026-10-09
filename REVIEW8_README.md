# Review 8 — NOT production validated

- SQL must be reviewed and applied in Supabase before Render deployment.
- `claim` happens before Garmin login; an `auth_failed` claim can be retried.
- Other statuses are blocked, including stale `in_progress` (manual reconciliation required).
- `finish` failure after Garmin success means state is uncertain: inspect Garmin Connect and Supabase before retry.
- No Garmin account tested; MFA and live scheduling remain unverified.
- This is a test candidate; do not deploy to production without end-to-end validation.
