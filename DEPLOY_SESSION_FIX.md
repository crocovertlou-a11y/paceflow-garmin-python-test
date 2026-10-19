# Garmin encrypted token session — staged rollout

1. Run SQL_GARMIN_SESSIONS.sql in Supabase (verify athlete_profiles.id is the correct referenced PK).
2. Generate a Fernet key securely and set GARMIN_SESSION_FERNET_KEY in Render only. Keep the existing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. Never put the key in Netlify or the client.
3. Deploy this ZIP to Render. This release intentionally fails closed if configuration is missing.
4. For an account with no stored session, one successful login exports encrypted OAuth tokens to Supabase. Later logins restore them before attempting password login.
5. A revoked/expired saved session fails closed; do not automatically retry passwords. Reauthorization requires a separate explicit controlled flow, not included here.
6. This does not clear or resend workouts whose ledger is auth_failed, in_progress, uncertain or partial. Reconcile before any new send.
7. Validate the garminconnect 0.3.19 garth dump/load API in staging first; offline unit tests cannot prove upstream behavior.
8. Tokens are sensitive; ensure backups and logs do not expose the table or encryption key. Rotate/revoke tokens and keys through an operational process.
