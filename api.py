from fastapi import FastAPI

app = FastAPI(title="PaceFlow Garmin Python Bridge")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "paceflow-garmin-python",
        "version": "0.1.0"
    }
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any

class WorkoutRequest(BaseModel):
    structured_workout: dict[str, Any]

@app.post("/workouts/prepare")
def prepare_workout(request: WorkoutRequest):
    workout = request.structured_workout

    if workout.get("valid") is not True:
        raise HTTPException(
            status_code=422,
            detail="Entrainement structure non valide"
        )

    return {
        "status": "prepared",
        "blocks_count": len(workout.get("blocks", [])),
        "garmin_sent": False
    }
from paceflow_mapping import convert_paceflow
from fastapi import HTTPException

@app.post("/workouts/convert")
def convert_workout(request: WorkoutRequest):
    try:
        converted = convert_paceflow(
            {"title": request.structured_workout.get("title", "Séance PaceFlow"), "structured_workout": request.structured_workout}
        )
        return {
            "status": "converted",
            "workout": converted,
            "garmin_sent": False
        }
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

from paceflow_mapping import convert_paceflow
from fastapi import HTTPException


@app.post("/workouts/simulate-send")
def simulate_send_workout(request: WorkoutRequest):
    from garmin_sender import send_workout

    converted = convert_paceflow({
        "title": request.structured_workout.get(
            "title", "Séance PaceFlow"
        ),
        "structured_workout": request.structured_workout,
    })

    class FakeGarmin:
        def upload_workout(self, payload):
            return {"workoutId": 12345}

        def schedule_workout(self, workout_id, date):
            return {"workoutScheduleId": 67890}

    result = send_workout(
        FakeGarmin(),
        converted,
        "2026-10-09"
    )

    return {
        "simulation": True,
        "garmin_sent": False,
        "result": result
    }

# Secure, read-only preview of the canonical Supabase workout.
# This endpoint NEVER creates or schedules a Garmin workout.
from fastapi import Header
from authorized_preview import preview_workout, AccessError

class AuthorizedPreviewRequest(BaseModel):
    workout_id: str
    athlete_id: str

@app.post('/workouts/authorized-preview')
def authorized_preview(request: AuthorizedPreviewRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Authentication required')
    try:
        return preview_workout(authorization[7:], request.workout_id, request.athlete_id)
    except AccessError:
        raise HTTPException(status_code=403, detail='Access denied or unavailable') from None
    except ValueError:
        raise HTTPException(status_code=422, detail='Invalid workout data') from None
