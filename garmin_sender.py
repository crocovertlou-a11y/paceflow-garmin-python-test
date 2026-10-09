"""Send a converted workout to Garmin Connect, with explicit partial-failure state."""

class GarminPartialSendError(RuntimeError):
    """Garmin created the workout but a subsequent step failed."""
    def __init__(self, workout_id, step):
        self.workout_id = workout_id
        self.step = step
        super().__init__(f'Garmin workout {workout_id} created; {step} failed')


def send_workout(client, payload, scheduled_date, push_device=False):
    if not isinstance(payload, dict):
        raise ValueError('Invalid Garmin workout payload')
    if not scheduled_date:
        raise ValueError('Missing scheduled date')
    result = client.upload_workout(payload)
    workout_id = result.get('workoutId') if isinstance(result, dict) else None
    if not workout_id:
        raise RuntimeError('Garmin did not return a workoutId')
    try:
        scheduled = client.schedule_workout(workout_id, scheduled_date)
    except Exception as exc:
        raise GarminPartialSendError(workout_id, 'scheduling') from exc
    response = {'status': 'scheduled', 'workout_id': workout_id,
                'date': scheduled_date,
                'schedule_id': scheduled.get('workoutScheduleId') if isinstance(scheduled, dict) else None}
    if push_device:
        try:
            response['device_push'] = client.push_workout_to_device(workout_id)
        except Exception as exc:
            raise GarminPartialSendError(workout_id, 'device push') from exc
    return response
