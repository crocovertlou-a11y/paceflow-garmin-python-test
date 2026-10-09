"""Envoi d'une séance déjà convertie vers Garmin Connect.

Module indépendant de l'API HTTP.
Ne stocke aucun identifiant ni jeton.
"""

def send_workout(client, payload, scheduled_date, push_device=False):
    if not isinstance(payload, dict):
        raise ValueError("Invalid Garmin workout payload")

    if not scheduled_date:
        raise ValueError("Missing scheduled date")

    result = client.upload_workout(payload)
    workout_id = result.get("workoutId")

    if not workout_id:
        raise RuntimeError("Garmin did not return a workoutId")

    scheduled = client.schedule_workout(workout_id, scheduled_date)

    response = {
        "status": "scheduled",
        "workout_id": workout_id,
        "date": scheduled_date,
        "schedule_id": scheduled.get("workoutScheduleId")
            if isinstance(scheduled, dict) else None,
    }

    if push_device:
        response["device_push"] = client.push_workout_to_device(workout_id)

    return response
