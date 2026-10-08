# PaceFlow v0.10.12 → Garmin Python (isolated mapping)

This is an **offline converter only**. It does not connect to Supabase or Garmin, does not upload workouts, and does not modify PaceFlow or Nolio.

PaceFlow workout format was checked against `workout-record.mjs`, `index.html` and `nolio-send-workout.mjs` in the supplied v0.10.12 ZIP.

- Input: a workout object with `title`, `structured_workout.valid === true`, and `structured_workout.blocks`.
- Steps: `kind` = `warmup`, `work`, `recovery`, `cooldown`; `duration` = `{value, unit}` with km/m/min/sec.
- Repetitions: `{kind:'repeat',repeat:N,children:[...]}`.
- Targets: `pace` or `pace_range`; heart rate and other target types are rejected, not silently discarded.
- Output: Garmin workout DTO with expanded steps; no upload or schedule action.

## iPad Codespaces

Upload `paceflow_mapping.py` and `test_paceflow_mapping.py` to the **test repository** next to `adapter.py`, then run:

```sh
python -m unittest -v test_adapter test_paceflow_mapping
```

## Security and production gates

Existing PaceFlow already includes Nolio functions and an older JS Garmin connector. Do **not** deploy this Python package to Netlify's static publish root. Before multi-athlete production use: athlete-owned Garmin consent and session storage, server-side authorization, encryption, rate limiting/backoff for HTTP 429, idempotency, audit trail, and a managed Python host (Codespaces is a development environment, not a production service). Official Garmin approval and terms should be evaluated before offering this commercially. Nolio remains unchanged.
