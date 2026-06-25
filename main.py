import os
import base64
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from core.engine import TTSEngine
from core.queue import tts_queue
from core.recorder import RecordingManager

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "nexmeet-secret-key")

app = FastAPI(title="KokoClone TTS Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("NEXMEET_URL", "http://localhost:8000")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

recorder = RecordingManager()


# ─── Auth ─────────────────────────────────────────────────────────────────────
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Geçersiz API key")
    return x_api_key


# ─── Models ───────────────────────────────────────────────────────────────────
class SynthesizeRequest(BaseModel):
    audio_base64: str
    peer_id: str
    source_lang: str = "tr"
    target_lang: str = "en"
    session_id: Optional[str] = None


class VoiceProfileRequest(BaseModel):
    audio_base64: str
    peer_id: str


class RecordingStartRequest(BaseModel):
    session_id: str
    peer_ids: list[str]


class RecordingStopRequest(BaseModel):
    session_id: str


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    engine = TTSEngine.get_instance()
    await engine.initialize()
    logger.info("✅ KokoClone TTS servisi hazır")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)

    # Base64 → ses dosyası
    audio_bytes = base64.b64decode(req.audio_base64)
    tmp_input = f"/tmp/input_{req.peer_id}_{int(time.time())}.wav"
    tmp_output = f"/tmp/output_{req.peer_id}_{int(time.time())}.wav"

    with open(tmp_input, "wb") as f:
        f.write(audio_bytes)

    engine = TTSEngine.get_instance()
    start = time.time()

    try:
        result = await engine.process_speech(
            audio_path=tmp_input,
            speaker_peer_id=req.peer_id,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
            output_path=tmp_output,
        )

        if not result:
            raise HTTPException(status_code=500, detail="TTS başarısız")

        duration_ms = int((time.time() - start) * 1000)

        # Kayıt aktifse chunk ekle
        if req.session_id:
            await recorder.add_chunk(req.session_id, tmp_output)

        # Ses → base64
        with open(tmp_output, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()

        return {
            "audio_base64": audio_b64,
            "duration_ms": duration_ms,
        }

    finally:
        for f in [tmp_input, tmp_output]:
            if os.path.exists(f):
                os.remove(f)


@app.post("/voice-profile")
async def save_voice_profile(req: VoiceProfileRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)

    audio_bytes = base64.b64decode(req.audio_base64)
    tmp_path = f"/tmp/profile_{req.peer_id}.wav"

    with open(tmp_path, "wb") as f:
        f.write(audio_bytes)

    engine = TTSEngine.get_instance()
    success = await engine.save_voice_profile(req.peer_id, tmp_path)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    if not success:
        raise HTTPException(status_code=500, detail="Profil kaydedilemedi")

    return {"success": True, "message": "Ses profili kaydedildi"}


@app.get("/voice-profile/{peer_id}")
async def get_voice_profile(peer_id: str, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    engine = TTSEngine.get_instance()
    exists = engine.has_voice_profile(peer_id)
    return {"exists": exists}


@app.post("/recording/start")
async def start_recording(req: RecordingStartRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    await recorder.start(req.session_id, req.peer_ids)
    return {"success": True}


@app.post("/recording/stop")
async def stop_recording(req: RecordingStopRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    output_path = await recorder.stop(req.session_id)
    if not output_path:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    return {"download_url": f"/recording/download/{req.session_id}"}


@app.get("/recording/download/{session_id}")
async def download_recording(session_id: str, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    path = recorder.get_recording_path(session_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")

    response = FileResponse(
        path,
        filename=f"toplanti_{session_id[:8]}.ogg",
        media_type="audio/ogg"
    )

    # İndirildikten sonra sil
    async def cleanup():
        if os.path.exists(path):
            os.remove(path)
        recorder.remove_session(session_id)

    response.background = cleanup
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "5000")), reload=True)
