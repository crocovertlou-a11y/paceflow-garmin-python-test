# Review 7 — SQL ledger preparation only

NOT READY TO DEPLOY. Contains a SQL migration and an idempotency.py RPC client, but api.py does NOT invoke them yet. Existing 23 tests pass but do not cover durable idempotency. Do not execute SQL without reviewing compatibility with live schema and backup. No real Garmin test performed.

Next: integrate claim before Garmin login, persist final states on all branches, ensure no password logging, test Supabase RPC with two concurrent requests and worker restarts, test MFA and partial-send recovery.
