# Garmin activity return — read-only prototype

POST /activities/candidates with Bearer Supabase athlete token and JSON keys: workout_id, athlete_id, email, password, optional mfa_code.

The endpoint checks athlete ownership of the canonical workout, then fetches Garmin activities within +/- 2 days of its scheduled date. It returns possible candidates only, never confirms a match or writes anything to Garmin or Supabase. Garmin credentials are not persisted. Avoid request-body logging.

Not yet integrated with PaceFlow UI. Test on Render with a real Garmin account before deploying into production. GarminConnect is an unofficial API and may change. Do not expose this endpoint without HTTPS and existing Supabase verification.
