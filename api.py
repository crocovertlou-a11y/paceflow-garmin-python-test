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

