import os
import time
import asyncio
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

VOICE_PROFILES_DIR = Path("voice_profiles")
VOICE_PROFILES_DIR.mkdir(exist_ok=True)


class TTSEngine:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.kokoro = None
        self.stt_model = None
        self._speaker_cache: Dict[str, Tuple[str, float]] = {}
        self._cache_ttl = 3600
        self._initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TTSEngine()
        return cls._instance

    async def initialize(self):
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            logger.info("Whisper yükleniyor...")
            import whisper
            self.stt_model = whisper.load_model("small")

            logger.info("KokoClone yükleniyor...")
            from core.cloner import KokoClone
            self.kokoro = KokoClone()

            self._initialized = True
            logger.info("✅ TTS Engine hazır")

    # ─── Ses Profili ──────────────────────────────────────────────────────────
    def _peer_hash(self, peer_id: str) -> str:
        return hashlib.md5(peer_id.encode()).hexdigest()

    def get_profile_path(self, peer_id: str) -> Path:
        return VOICE_PROFILES_DIR / f"{self._peer_hash(peer_id)}.wav"

    def has_voice_profile(self, peer_id: str) -> bool:
        return self.get_profile_path(peer_id).exists()

    async def save_voice_profile(self, peer_id: str, wav_path: str) -> bool:
        try:
            profile_path = self.get_profile_path(peer_id)
            shutil.copy2(wav_path, str(profile_path))
            # RAM cache güncelle
            self._speaker_cache[peer_id] = (str(profile_path), time.time())
            logger.info(f"Ses profili kaydedildi: {peer_id}")
            return True
        except Exception as e:
            logger.error(f"Profil kayıt hatası: {e}")
            return False

    def get_voice_path(self, peer_id: str) -> Optional[str]:
        # Önce RAM cache
        if peer_id in self._speaker_cache:
            path, ts = self._speaker_cache[peer_id]
            if time.time() - ts < self._cache_ttl and os.path.exists(path):
                return path
        # Sonra disk
        profile_path = self.get_profile_path(peer_id)
        if profile_path.exists():
            path = str(profile_path)
            self._speaker_cache[peer_id] = (path, time.time())
            return path
        return None

    # ─── STT ──────────────────────────────────────────────────────────────────
    async def transcribe(self, audio_path: str, language: str = "tr") -> str:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.stt_model.transcribe(audio_path, language=language)
        )
        text = result["text"].strip()
        logger.info(f"STT: {text}")
        return text

    # ─── Çeviri ───────────────────────────────────────────────────────────────
    async def translate(self, text: str, source_lang: str = "tr", target_lang: str = "en") -> str:
        try:
            from deep_translator import GoogleTranslator
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: GoogleTranslator(
                    source=source_lang[:2].lower(),
                    target=target_lang[:2].lower()
                ).translate(text)
            )
            translated = result or text
            logger.info(f"Çeviri: {text} → {translated}")
            return translated
        except Exception as e:
            logger.error(f"Çeviri hatası: {e}")
            return text

    # ─── TTS ──────────────────────────────────────────────────────────────────
    async def synthesize(self, text: str, peer_id: str, output_path: str) -> bool:
        voice_path = self.get_voice_path(peer_id)

        async with self._lock:
            loop = asyncio.get_event_loop()
            try:
                if voice_path:
                    # Ses klonuyla üret
                    await loop.run_in_executor(
                        None,
                        lambda: self.kokoro.generate(
                            text=text,
                            lang="en",
                            reference_audio=voice_path,
                            output_path=output_path,
                        )
                    )
                else:
                    # Varsayılan sesle üret
                    await loop.run_in_executor(
                        None,
                        lambda: self.kokoro.generate(
                            text=text,
                            lang="en",
                            output_path=output_path,
                        )
                    )
                return True
            except Exception as e:
                logger.error(f"TTS hatası: {e}")
                return False

    # ─── Ana Pipeline ─────────────────────────────────────────────────────────
    async def process_speech(
        self,
        audio_path: str,
        speaker_peer_id: str,
        source_lang: str = "tr",
        target_lang: str = "en",
        output_path: str = "/tmp/tts_output.wav"
    ) -> Optional[str]:
        # STT ve ses profili yükleme paralel
        transcribe_task = asyncio.create_task(
            self.transcribe(audio_path, language=source_lang)
        )
        voice_path = self.get_voice_path(speaker_peer_id)  # 0ms (cache'den)

        text = await transcribe_task
        if not text:
            logger.warning("STT boş sonuç döndü")
            return None

        translated = await self.translate(text, source_lang, target_lang)
        if not translated:
            return None

        success = await self.synthesize(translated, speaker_peer_id, output_path)
        if not success:
            return None

        return output_path
