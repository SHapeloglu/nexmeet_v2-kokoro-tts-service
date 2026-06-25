import os
import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp_recordings")
RECORDINGS_DIR = Path("recordings")
TEMP_DIR.mkdir(exist_ok=True)
RECORDINGS_DIR.mkdir(exist_ok=True)

RECORDING_TTL = 86400  # 24 saat


class RecordingManager:
    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    async def start(self, session_id: str, peer_ids: List[str]):
        session_dir = TEMP_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        self._sessions[session_id] = {
            "peer_ids": peer_ids,
            "chunks": [],
            "started_at": time.time(),
            "dir": str(session_dir),
        }
        logger.info(f"Kayıt başladı: {session_id}")

    async def add_chunk(self, session_id: str, audio_path: str):
        if session_id not in self._sessions:
            return
        session = self._sessions[session_id]
        chunk_index = len(session["chunks"])
        dest = Path(session["dir"]) / f"chunk_{chunk_index:04d}.wav"
        # Kopyala
        import shutil
        shutil.copy2(audio_path, str(dest))
        session["chunks"].append(str(dest))

    async def stop(self, session_id: str) -> Optional[str]:
        if session_id not in self._sessions:
            return None

        session = self._sessions[session_id]
        chunks = session["chunks"]

        if not chunks:
            return None

        output_path = str(RECORDINGS_DIR / f"{session_id}.ogg")

        try:
            # Chunk listesi dosyası oluştur (ffmpeg için)
            list_file = Path(session["dir"]) / "chunks.txt"
            with open(str(list_file), "w") as f:
                for chunk in chunks:
                    f.write(f"file '{chunk}'\n")

            # ffmpeg: tüm chunk'ları birleştir + OPUS encode
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c:a", "libopus",
                "-b:a", "64k",
                output_path
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()

            if proc.returncode != 0:
                raise Exception("ffmpeg başarısız")

            # Temp klasörü sil
            import shutil
            shutil.rmtree(session["dir"], ignore_errors=True)

            logger.info(f"Kayıt tamamlandı: {session_id} → {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Kayıt birleştirme hatası: {e}")
            return None

    def get_recording_path(self, session_id: str) -> Optional[str]:
        path = str(RECORDINGS_DIR / f"{session_id}.ogg")
        return path if os.path.exists(path) else None

    def remove_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    async def cleanup_expired(self):
        """Süresi dolmuş kayıtları temizle."""
        now = time.time()
        for f in RECORDINGS_DIR.glob("*.ogg"):
            if now - f.stat().st_mtime > RECORDING_TTL:
                f.unlink()
                logger.info(f"TTL doldu, silindi: {f.name}")
