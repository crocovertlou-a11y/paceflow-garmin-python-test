# Garmin authentication failure guard — 2026-10-19

Changes: treat Garmin 403 Cloudflare challenge as a temporary block, like 429; enforce a 30-minute process-local cooldown after either refusal, before any subsequent login or durable claim. The cooldown does not persist across Render restarts or workers and does not bypass Garmin protections. First failed login can still take time because garminconnect may try multiple strategies internally.

This release does NOT implement reusable Garmin session persistence: that would require an explicit encrypted, athlete-scoped credential/token lifecycle and a security review. It does NOT solve Garmin blocking or automatically reconcile an already in_progress send. Do not retry the existing workout until ledger status and Garmin Connect are reconciled.

Deploy Render project only. No Netlify or Supabase changes. Tests: python -m unittest test_auth_cooldown.py. No live Garmin send performed.
