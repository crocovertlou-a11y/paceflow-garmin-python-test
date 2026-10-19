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


# Real send: Python owns the entire Garmin API interaction. No credential persistence.
# Athlete ownership and canonical workout are verified by Supabase on every request.
from pydantic import Field
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import date
from threading import Lock

_send_guard = Lock()
_inflight_workouts = set()  # process-local only; NOT durable idempotency

class GarminSendRequest(BaseModel):
    workout_id: str
    athlete_id: str
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)
    mfa_code: str | None = Field(default=None, max_length=24)

@app.post('/workouts/send')
def send_canonical_workout(request: GarminSendRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Connexion PaceFlow requise')
    try:
        canonical = preview_workout(authorization[7:], request.workout_id, request.athlete_id, athlete_only=True)
    except AccessError:
        raise HTTPException(status_code=403, detail='Envoi réservé à cet athlète') from None
    except ValueError:
        raise HTTPException(status_code=422, detail='Séance invalide') from None
    try:
        date.fromisoformat(canonical['scheduled_date'])
    except ValueError:
        raise HTTPException(status_code=422, detail='Date invalide') from None
    # Block a new send before taking a durable claim when Garmin is in cooldown.
    _guard_garmin_login()
    from idempotency import claim, finish, AlreadyClaimed, LedgerError
    from garminconnect import Garmin
    from garmin_sender import send_workout, GarminPartialSendError
    athlete_id = canonical['athlete_id']
    workout_id = request.workout_id
    # Durable claim BEFORE login, across workers and restarts.
    try:
        claim(athlete_id, workout_id)
    except AlreadyClaimed:
        raise HTTPException(status_code=409, detail='Séance déjà traitée ou envoi incertain. Vérifie Garmin Connect.') from None
    except LedgerError:
        raise HTTPException(status_code=503, detail='Registre indisponible : aucun envoi Garmin effectué.') from None

    def complete(status, garmin_id=None):
        try:
            finish(athlete_id, workout_id, status, garmin_id)
        except LedgerError:
            # Never claim success if durable result could not be recorded.
            raise HTTPException(status_code=503, detail='État de transfert incertain : vérifie Garmin Connect avant de réessayer.') from None

    class MFARequired(Exception):
        pass

    def prompt_mfa():
        if not request.mfa_code or not request.mfa_code.strip():
            raise MFARequired()
        return request.mfa_code.strip()

    try:
        client = Garmin(request.email, request.password, prompt_mfa=prompt_mfa)
        client.login()
    except MFARequired:
        complete('auth_failed')
        raise HTTPException(status_code=428, detail='Code MFA Garmin requis. Renseigne le code puis reconnecte-toi.') from None
    except Exception as exc:
        from garmin_auth_errors import classify_login_error
        classification = classify_login_error(exc)
        if classification == 'rate_limited':
            # The Garmin request was rejected before upload. Preserve ledger
            # semantics and prevent immediate new attempts on this worker.
            complete('auth_failed')
            _garmin_login_failure(exc)
        if classification == 'auth_failed':
            complete('auth_failed')
            raise HTTPException(status_code=401,
                detail='Identifiants Garmin refusés. Vérifie-les avant un nouvel essai.') from None
        # Ambiguous failures must not be treated as invalid credentials.
        complete('auth_failed')
        raise HTTPException(status_code=503,
            detail='Authentification Garmin indisponible. Aucun envoi effectué; vérifie le registre avant toute nouvelle tentative.') from None
    try:
        result = send_workout(client, canonical['garmin_workout'], canonical['scheduled_date'])
    except GarminPartialSendError as exc:
        complete('partial', exc.workout_id)
        raise HTTPException(status_code=409, detail=f'Séance créée sur Garmin (ID {exc.workout_id}), programmation non confirmée. Vérifie Garmin Connect.') from None
    except Exception:
        complete('uncertain')
        raise HTTPException(status_code=502, detail='Résultat Garmin incertain. Vérifie Garmin Connect avant de réessayer.') from None
    complete('sent', result['workout_id'])
    return {'ok': True, 'workoutId': result['workout_id'], 'scheduled': True,
            'athlete_id': canonical['athlete_id'], 'date': canonical['scheduled_date'],
            'name': canonical['garmin_workout']['workoutName'], 'provider': 'python'}

# Best-effort process-local cooldown: avoids repeat logins on a warm worker.
# This does not bypass Garmin rate limits and is not shared between Render workers.
import threading
import time
_garmin_cooldown_lock = threading.Lock()
_garmin_cooldown_until = 0.0
_GARMIN_AUTH_COOLDOWN_SECONDS = 1800

def _guard_garmin_login():
    with _garmin_cooldown_lock:
        remaining = _garmin_cooldown_until - time.monotonic()
    if remaining > 0:
        raise HTTPException(status_code=429,
            detail='Garmin limite temporairement les connexions. Attends avant de réessayer.',
            headers={'Retry-After': str(max(1, int(remaining) + 1))})

def _garmin_login_failure(exc):
    global _garmin_cooldown_until
    from garmin_auth_errors import classify_login_error
    classification = classify_login_error(exc)
    if classification == 'rate_limited':
        with _garmin_cooldown_lock:
            _garmin_cooldown_until = max(_garmin_cooldown_until, time.monotonic() + _GARMIN_AUTH_COOLDOWN_SECONDS)
        raise HTTPException(status_code=429,
            detail='Garmin refuse temporairement la connexion (429 ou protection 403). Aucun envoi confirmé. Ne relance pas cette séance; vérifie Garmin Connect et le registre.',
            headers={'Retry-After': str(_GARMIN_AUTH_COOLDOWN_SECONDS)}) from None
    if classification == 'auth_failed':
        raise HTTPException(status_code=401,
            detail='Identifiants Garmin refusés. Vérifie-les avant un nouvel essai.') from None
    raise HTTPException(status_code=502,
        detail='Connexion Garmin indisponible. Aucun résultat enregistré.') from None

# Garmin return POC: read-only candidates; no matching or persistence.
from datetime import timedelta

class GarminActivityCandidatesRequest(BaseModel):
    workout_id: str
    athlete_id: str
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)
    mfa_code: str | None = Field(default=None, max_length=24)

@app.post('/activities/candidates')
def garmin_activity_candidates(request: GarminActivityCandidatesRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Connexion PaceFlow requise')
    try:
        canonical = preview_workout(authorization[7:], request.workout_id, request.athlete_id, athlete_only=True)
    except AccessError:
        raise HTTPException(status_code=403, detail='Accès réservé à cet athlète') from None
    except ValueError:
        raise HTTPException(status_code=422, detail='Séance invalide') from None
    try:
        target = date.fromisoformat(canonical['scheduled_date'])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=422, detail='Date de séance invalide') from None
    from garminconnect import Garmin
    class MFARequired(Exception):
        pass
    def prompt_mfa():
        if not request.mfa_code or not request.mfa_code.strip():
            raise MFARequired()
        return request.mfa_code.strip()
    _guard_garmin_login()
    try:
        client = Garmin(request.email, request.password, prompt_mfa=prompt_mfa)
        client.login()
    except MFARequired:
        raise HTTPException(status_code=428, detail='Code MFA Garmin requis') from None
    except Exception as exc:
        _garmin_login_failure(exc)
    start = (target - timedelta(days=2)).isoformat()
    end = (target + timedelta(days=2)).isoformat()
    try:
        activities = client.get_activities_by_date(start, end)
    except Exception:
        raise HTTPException(status_code=502, detail='Lecture des activités Garmin impossible') from None
    if not isinstance(activities, list):
        raise HTTPException(status_code=502, detail='Réponse Garmin inattendue')
    from garmin_activity_matching import normalize_candidates
    candidates = normalize_candidates(activities, target)
    return {'ok': True, 'workout_id': request.workout_id,
            'athlete_id': canonical['athlete_id'], 'scheduled_date': target.isoformat(),
            'search_start': start, 'search_end': end, 'candidates': candidates,
            'confirmed': False, 'saved': False}
