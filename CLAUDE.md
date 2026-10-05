# CLAUDE.md

Bu dosya, bu proje üzerinde çalışırken Claude'un (Claude Code dahil) izlemesi gereken bağlamı ve kuralları içerir.

## Proje

**🎙️ NexMeet Kokoro TTS Service** — Gerçek zamanlı video konferans için **ses klonlamalı konuşma çevirisi** servisi. Kullanıcı kendi sesinde **Türkçe** konuşur → sistem otomatik olarak **İngilizce**'ye çevirir ve konuşmacının **klonlanmış sesiyle** karşı tarafa iletir.

- GitHub: https://github.com/SHapeloglu/nexmeet_v2-kokoro-tts-service

## Teknoloji Yığını

- FastAPI
- PyTorch
- OpenAI API
- Uvicorn
- Docker / docker compose

## Önemli Dosyalar

- `Dockerfile`
- `kokoro-tts.service`
- `main.py`
- `requirements.txt`

Mimari ayrıntılar için bkz. `architect.md`.

## Sık Kullanılan Komutlar

```bash
python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
python main.py
```

## Kurallar

- Yapılandırmayı ortam değişkenlerinden oku; endpoint şemalarını Pydantic modelleriyle tanımla.
- Bloklayan I/O işlemlerini async endpoint içinde doğrudan çağırma.
- `.env`, parola, token ve API anahtarlarını asla commit etme.
- Her çalışma oturumunun sonunda `session.md`ye kısa kayıt düş; görev durumunu `task.md`de güncelle.
- Önceliklendirilmemiş fikirleri `backlog.md`ye yaz; somutlaşınca `task.md`ye taşı.

## Çalışma Dosyaları

| Dosya | Amaç |
|---|---|
| `architect.md` | Mimari ve dizin yapısı referansı |
| `task.md` | Aktif / devam eden / tamamlanan görevler |
| `backlog.md` | Önceliklendirilmemiş fikir ve teknik borç havuzu |
| `session.md` | Oturum günlüğü — her oturum sonunda güncellenir |
