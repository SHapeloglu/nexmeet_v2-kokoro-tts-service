# architect.md — 🎙️ NexMeet Kokoro TTS Service Mimari Referansı

Bu dosya projenin yapısının hızlı-referans özetidir. Kod değiştikçe güncel tutun.

## Genel Bakış

Gerçek zamanlı video konferans için **ses klonlamalı konuşma çevirisi** servisi. Kullanıcı kendi sesinde **Türkçe** konuşur → sistem otomatik olarak **İngilizce**'ye çevirir ve konuşmacının **klonlanmış sesiyle** karşı tarafa iletir.

## Teknoloji Yığını

- FastAPI
- PyTorch
- OpenAI API
- Uvicorn
- Docker / docker compose

## Dizin Yapısı

```
.env.example
.gitignore
Dockerfile
README.md
core/
  __init__.py
  chunker.py
  cloner.py
  engine.py
  queue.py
  recorder.py
kokoro-tts.service
main.py
requirements.txt
```

## Modüller / Kaynak Dosyalar

- `main.py`
- `core/chunker.py`
- `core/cloner.py`
- `core/engine.py`
- `core/queue.py`
- `core/recorder.py`

## Giriş Noktaları ve Yapılandırma

- `Dockerfile`
- `kokoro-tts.service`
- `main.py`
- `requirements.txt`

## Dağıtım / Çalışma Ortamı

- GitHub: https://github.com/SHapeloglu/nexmeet_v2-kokoro-tts-service

## Diğer Dokümanlar

- `README.md`

## Mimari Kararlar

_Önemli tasarım kararlarını ve gerekçelerini buraya ekleyin (ör. "X yerine Y seçildi çünkü ...")._
