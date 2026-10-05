# architect.md — NexMeet Kokoro TTS Service (v2) Mimarisi

```
NexMeet backend ──X-API-Key──► main.py (FastAPI, 0.0.0.0:5000, EC2 g4dn)
   startup → TTSEngine.get_instance().initialize()  (Whisper "small" + TTS modeli yüklenir)
   POST /synthesize ─► tts_queue ─► TTSEngine.process_speech
        transcribe (whisper) → translate (deep-translator) → synthesize (KokoClone/ChatterboxTTS, konuşmacı profili ile)
        → RecordingManager (oturum kaydı)
   POST /voice-profile → profil WAV (peer hash'i ile dosya adı)
   GET  /voice-profile/{peer_id}, GET /health
```

| Dosya | Rol |
|---|---|
| `main.py` | FastAPI uç noktaları, API anahtarı, startup |
| `core/engine.py` | `TTSEngine` tekil nesne: STT, çeviri, sentez, profil yolu (`_peer_hash`), konuşmacı önbelleği (1 saat TTL) |
| `core/cloner.py` | `KokoClone` → `ChatterboxTTS.from_pretrained(device=cuda/cpu)` |
| `core/queue.py`, `core/chunker.py` | İstek kuyruğu, ses parçalama |
| `core/recorder.py` | Oturum kayıtları |
| `Dockerfile`, `kokoro-tts.service` | Dağıtım |

## Mimari Kararlar

- **Ses klonlama için GPU** — gerçek zamanlıya yakın gecikme için T4 gerekli.
- **Profil dosya adı hash'li** (`_peer_hash`) — v3'teki doğrudan `peer_id` kullanımından daha güvenli.
- v3'te maliyet nedeniyle CPU Kokoro'ya geçildi; bu repo GPU seçeneği için referans.
