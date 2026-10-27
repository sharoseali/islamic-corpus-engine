"""Speech-to-text endpoint for voice search."""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services import speech

router = APIRouter(prefix="/speech", tags=["speech"])

# About a minute of compressed speech; clips are capped at 20s client side.
MAX_AUDIO_BYTES = 5 * 1024 * 1024


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(..., description="Recorded speech clip"),
    lang: str = Query("ur", pattern="^(ar|ur|en)$"),
) -> dict:
    data = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio clip too large")
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio clip")
    try:
        text = await run_in_threadpool(speech.transcribe, data, lang)
    except speech.SpeechUnavailable as exc:
        raise HTTPException(status_code=503, detail="Voice search is not set up on this server") from exc
    except Exception as exc:  # decoding or model errors
        raise HTTPException(status_code=422, detail="Could not transcribe audio") from exc
    return {"text": text, "language": lang}
