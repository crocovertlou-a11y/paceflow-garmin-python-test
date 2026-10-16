# Garmin return V3 — local review logic

`assess_candidate()` adds explainable review flags for date, sport and distance, but never approves a match. Thresholds of 5% and 20% are heuristic indicators, not medical or training conclusions. Expected distance must include recovery segments where applicable; otherwise omit expected_distance_m. This logic is not yet connected to the PaceFlow interface. Existing /activities/candidates remains read-only and returns candidates requiring athlete confirmation. No live Garmin test has been performed.

Local tests: `python -m unittest discover -q` (31 tests).
