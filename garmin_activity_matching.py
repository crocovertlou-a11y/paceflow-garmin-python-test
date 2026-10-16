
"""Read-only candidate normalization and conservative matching hints.

Hints are not proof of identity. The athlete must explicitly confirm.
"""
from datetime import date, datetime
from math import isfinite

RUNNING = {"running", "trail_running", "treadmill_running", "track_running", "virtual_run"}
CYCLING = {"cycling", "road_biking", "indoor_cycling", "mountain_biking"}
SWIMMING = {"lap_swimming", "open_water_swimming"}

def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        return None
    return value

def normalize_candidates(activities, target_date):
    if not isinstance(activities, list):
        raise ValueError("Unexpected Garmin response")
    results = []
    seen = set()
    for item in activities[:100]:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("activityId")
        if isinstance(raw_id, bool) or not isinstance(raw_id, (int, str)) or not str(raw_id).isdigit():
            continue
        activity_id = str(raw_id)
        if activity_id in seen:
            continue
        seen.add(activity_id)
        raw_type = item.get("activityType")
        sport = raw_type.get("typeKey") if isinstance(raw_type, dict) else None
        start = item.get("startTimeLocal")
        day_delta = None
        if isinstance(start, str):
            try:
                day_delta = abs((date.fromisoformat(start[:10]) - target_date).days)
            except ValueError:
                pass
        results.append({
            "activity_id": activity_id,
            "name": str(item.get("activityName") or "")[:200],
            "start_time_local": start if isinstance(start, str) else None,
            "sport": sport if isinstance(sport, str) else None,
            "distance_m": _number(item.get("distance")),
            "duration_s": _number(item.get("duration")),
            "moving_duration_s": _number(item.get("movingDuration")),
            "average_hr": _number(item.get("averageHR")),
            "max_hr": _number(item.get("maxHR")),
            "date_difference_days": day_delta,
            "match_status": "candidate_only",
            "requires_athlete_confirmation": True,
        })
    return sorted(results, key=lambda x: (x["date_difference_days"] is None,
                                          x["date_difference_days"] if x["date_difference_days"] is not None else 99,
                                          x["start_time_local"] or "", x["activity_id"]))


def assess_candidate(candidate, *, expected_sport=None, expected_distance_m=None):
    """Conservative explainable review, never an automatic match or approval."""
    reasons = []
    checks = {}
    delta = candidate.get('date_difference_days')
    checks['date'] = 'unknown' if delta is None else ('same_day' if delta == 0 else 'nearby')
    if delta is None:
        reasons.append('Date Garmin manquante ou illisible')
    elif delta > 0:
        reasons.append(f'Activité à {delta} jour(s) de la date prescrite')
    actual_sport = candidate.get('sport')
    groups = {'running': RUNNING, 'cycling': CYCLING, 'swimming': SWIMMING}
    if expected_sport is not None:
        if expected_sport not in groups:
            checks['sport'] = 'unknown'
        elif not actual_sport:
            checks['sport'] = 'unknown'
            reasons.append('Type de sport Garmin indisponible')
        elif actual_sport not in groups[expected_sport]:
            checks['sport'] = 'different'
            reasons.append('Sport différent de la prescription')
        else:
            checks['sport'] = 'compatible'
    actual_distance = candidate.get('distance_m')
    if expected_distance_m is not None:
        if not isinstance(expected_distance_m, (int, float)) or expected_distance_m <= 0 or not isfinite(expected_distance_m):
            raise ValueError('Invalid expected distance')
        if actual_distance is None:
            checks['distance'] = 'unknown'
            reasons.append('Distance Garmin indisponible')
        else:
            deviation = abs(actual_distance - expected_distance_m) / expected_distance_m
            checks['distance'] = 'large_difference' if deviation > .20 else ('difference' if deviation > .05 else 'close')
            if deviation > .05:
                reasons.append(f'Écart de distance de {deviation * 100:.0f}% (récupérations ou modifications possibles)')
    return {'checks': checks, 'review_reasons': reasons,
            'requires_athlete_confirmation': True, 'automatic_match': False}
