# CLAUDE.md — NexMeet Kokoro TTS Service (v2, GPU tasarımı — arşiv)

NexMeet v2 için tasarlanan **ses klonlamalı** konuşma çevirisi servisi: Whisper **small** (STT) → deep-translator (TR→EN) → **ChatterboxTTS** ile konuşmacının klonlanmış sesi (`core/cloner.py`, CUDA varsa GPU). Hedef ortam AWS EC2 g4dn.xlarge (NVIDIA T4), `/home/ubuntu/kokoro-tts-service`, systemd `kokoro-tts.service`, port 5000. Ek: kuyruk (`core/queue.py`), parçalama (`core/chunker.py`), kayıt yöneticisi (`core/recorder.py`).

- GitHub: https://github.com/SHapeloglu/nexmeet_v2-kokoro-tts-service — **PUBLIC repo** (tek yükleme, 2026-06-25)
- **Canlıda kullanılan servis bu değil:** `/root/nexmeet-tts` (repo `nexmeet-tts_v3`) — CPU'da Kokoro ONNX + faster-whisper tiny, ses klonlama yok. GPU maliyeti nedeniyle bu tasarım askıda.
- Mimari: `architect.md` · Görevler: `task.md` · Fikirler: `backlog.md` · Günlük: `session.md`

## Çalıştırma (GPU'lu makinede)

```bash
python -m venv venv && . venv/bin/activate && pip install -r requirements.txt   # torch 2.6, openai-whisper, kokoro-onnx
cp .env.example .env     # API_KEY, NEXMEET_URL, PORT, HOST
uvicorn main:app --host 0.0.0.0 --port 5000     # ya da kokoro-tts.service
```

## Kurallar

- Bu repoda değişiklik yapmadan önce kullanıcıya sor; canlı TTS işi `/root/nexmeet-tts`'te.
- API sözleşmesi (`/synthesize`, `/voice-profile`, `/voice-profile/{peer_id}`, `/health`, `X-API-Key`) v3 ile aynı — sözleşmeyi değiştirirsen ikisini birlikte değiştir.
- `requirements.txt`'te `chatterbox` paketi yok ama `core/cloner.py` import ediyor — kurulumda ayrıca gerekli.
- Public repo: `.env`, IP, anahtar commit etme.
