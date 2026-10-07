# 🎙️ NexMeet Kokoro TTS Service

> 🗄️ **ARŞİV (2026-10-07):** Bu sürüm artık geliştirilmiyor. Güncel sürüm: **[SHapeloglu/nexmeet-tts_v3](https://github.com/SHapeloglu/nexmeet-tts_v3)** (canlı TTS servisi). Bağlanmamış ses klonlama ve kullanılmayan kayıt uçları v3 `backlog.md`'de not edildi.

Gerçek zamanlı video konferans için **ses klonlamalı konuşma çevirisi** servisi.

Kullanıcı kendi sesinde **Türkçe** konuşur → sistem otomatik olarak **İngilizce**'ye çevirir ve konuşmacının **klonlanmış sesiyle** karşı tarafa iletir.

---

## 🏗️ Mimari

```
Kullanıcı (Türkçe konuşur)
        │
        ▼
  [WebRTC / Mikrofon]
        │  ses chunk (base64)
        ▼
  NexMeet Backend (FastAPI)
        │  POST /synthesize
        ▼
  ┌─────────────────────────────────────┐
  │       KokoClone TTS Service         │
  │                                     │
  │  1. Whisper STT  → metin (TR)       │
  │  2. GoogleTranslator → metin (EN)   │
  │  3. ChatterboxTTS → ses (EN)        │
  │     (klonlanmış sesle)              │
  └─────────────────────────────────────┘
        │  audio_base64 (WAV)
        ▼
  Karşı taraf (İngilizce duyar,
               aynı ses tonu)
```

---

## 🧰 Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| API Framework | FastAPI + Uvicorn |
| STT (Konuşma → Metin) | OpenAI Whisper (`small` model) |
| Çeviri | deep-translator (Google Translate) |
| TTS (Metin → Ses) | ResembleAI Chatterbox (ses klonlama) |
| GPU | NVIDIA T4, CUDA, PyTorch 2.6.0 |
| Sunucu | AWS EC2 g4dn.xlarge |
| Python | 3.12 (venv) |

---

## 📁 Proje Yapısı

```
kokoro-tts-service/
├── main.py                  # FastAPI uygulama ve endpoint'ler
├── core/
│   ├── __init__.py
│   ├── engine.py            # Ana pipeline: STT → Çeviri → TTS
│   ├── cloner.py            # ChatterboxTTS ses klonlama
│   ├── chunker.py           # Ses chunk yönetimi
│   ├── queue.py             # TTS kuyruk sistemi
│   └── recorder.py          # Toplantı kayıt yöneticisi
├── voice_profiles/          # Kullanıcı ses profilleri (git'e dahil değil)
├── recordings/              # Toplantı kayıtları (git'e dahil değil)
├── temp_recordings/         # Geçici ses dosyaları (git'e dahil değil)
├── .env.example             # Ortam değişkenleri şablonu
├── .env                     # Ortam değişkenleri (git'e dahil değil)
├── requirements.txt         # Python bağımlılıkları
├── Dockerfile               # Docker image tanımı
└── kokoro-tts.service       # systemd servis dosyası
```

---

## ⚙️ Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayın ve doldurun:

```bash
cp .env.example .env
```

| Değişken | Açıklama | Örnek |
|----------|----------|-------|
| `API_KEY` | NexMeet backend ile paylaşılan gizli anahtar | `nexmeet-secret-key-123` |
| `NEXMEET_URL` | CORS için NexMeet backend URL'si | `https://nexmeet.powerbi.com.tr` |
| `PORT` | Servis portu | `5000` |
| `HOST` | Dinleme adresi | `0.0.0.0` |

> ⚠️ `API_KEY` değeri NexMeet backend'deki `.env` dosyasındaki `TTS_API_KEY` ile **birebir aynı** olmalıdır.

---

## 🚀 Kurulum (AWS EC2 g4dn.xlarge)

### 1. Sistem Gereksinimleri

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv ffmpeg git
```

> **ffmpeg zorunludur** — Whisper ses dosyalarını işlemek için kullanır.

### 2. Sanal Ortam Oluştur

```bash
cd /home/ubuntu
git clone https://github.com/SHapeloglu/nexmeet-kokoro-tts-service.git kokoro-tts-service
cd kokoro-tts-service

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ortam Değişkenlerini Ayarla

```bash
cp .env.example .env
nano .env
# API_KEY ve NEXMEET_URL değerlerini düzenle
```

### 4. systemd Servisi Olarak Kur

```bash
sudo cp kokoro-tts.service /etc/systemd/system/
sudo nano /etc/systemd/system/kokoro-tts.service
# PATH ve WorkingDirectory değerlerini kontrol et

sudo systemctl daemon-reload
sudo systemctl enable kokoro-tts.service
sudo systemctl start kokoro-tts.service
```

### 5. Servis Durumunu Kontrol Et

```bash
sudo systemctl status kokoro-tts.service
# "✅ KokoClone TTS servisi hazır" mesajını bekle
```

---

## 📡 API Endpoints

Tüm endpoint'ler `x-api-key` header'ı gerektirir.

### `GET /health`
Servis sağlık kontrolü.

```bash
curl http://localhost:5000/health
# {"status":"ok","timestamp":1234567890.0}
```

---

### `POST /synthesize`
Ana pipeline: ses → STT → çeviri → TTS (klonlanmış ses).

**Request:**
```json
{
  "audio_base64": "<WAV dosyasının base64 kodlaması>",
  "peer_id": "kullanici-id",
  "source_lang": "tr",
  "target_lang": "en",
  "session_id": "oturum-id"
}
```

**Response:**
```json
{
  "audio_base64": "<üretilen WAV dosyasının base64 kodlaması>",
  "duration_ms": 4200
}
```

**Test:**
```bash
# Önce test sesi oluştur
ffmpeg -f lavfi -i "sine=frequency=440:duration=2" -ar 16000 -ac 1 /tmp/test.wav -y

BASE64=$(base64 -w 0 /tmp/test.wav)

curl -X POST http://localhost:5000/synthesize \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d "{\"audio_base64\":\"$BASE64\",\"peer_id\":\"test\",\"source_lang\":\"tr\",\"target_lang\":\"en\"}"
```

---

### `POST /voice-profile`
Kullanıcının ses profilini kaydet (klonlama için referans ses).

**Request:**
```json
{
  "audio_base64": "<en az 3 saniyelik WAV, base64>",
  "peer_id": "kullanici-id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ses profili kaydedildi"
}
```

---

### `GET /voice-profile/{peer_id}`
Kullanıcının ses profilinin var olup olmadığını kontrol et.

**Response:**
```json
{
  "exists": true
}
```

---

### `POST /recording/start`
Toplantı kaydını başlat.

```json
{
  "session_id": "oturum-id",
  "peer_ids": ["peer1", "peer2"]
}
```

---

### `POST /recording/stop`
Toplantı kaydını durdur ve indirme URL'si al.

```json
{
  "session_id": "oturum-id"
}
```

---

### `GET /recording/download/{session_id}`
Kaydı OGG formatında indir (indirildikten sonra otomatik silinir).

---

## 🔄 Pipeline Detayı

`core/engine.py` — `process_speech()` metodu:

```
1. STT (Whisper small)
   └── audio_path → Türkçe metin
       └── ~1-2 saniye (GPU)

2. Çeviri (Google Translate via deep-translator)
   └── Türkçe metin → İngilizce metin
       └── ~0.5 saniye (network)

3. TTS (ChatterboxTTS / Chatterbox)
   └── İngilizce metin + referans ses → WAV
       └── ~2-3 saniye (GPU)

Toplam gecikme: ~4-6 saniye
```

### Ses Profili Cache

Ses profilleri hem RAM'de (`_speaker_cache`, 1 saatlik TTL) hem diskte (`voice_profiles/`) saklanır. RAM cache miss durumunda diskten yüklenir.

---

## 🔧 Sorun Giderme

### ffmpeg bulunamıyor
```bash
# Kontrol et
which ffmpeg

# PATH'e ekle (systemd için)
# /etc/systemd/system/kokoro-tts.service içinde:
Environment="PATH=/home/ubuntu/venv/bin:/usr/bin:/usr/local/bin:/bin"
```

### API key hatası (401)
```bash
# Servisteki key'i kontrol et
sudo cat /proc/$(systemctl show -p MainPID kokoro-tts.service | cut -d= -f2)/environ | tr '\0' '\n' | grep API_KEY

# NexMeet backend .env ile karşılaştır
grep TTS_API_KEY /home/ubuntu/nexmeet/NextMeet/.env
```

### Servis başlamıyor
```bash
sudo journalctl -u kokoro-tts.service -n 50 --no-pager
```

### GPU kullanımını kontrol et
```bash
nvidia-smi
```

---

## 🔒 Güvenlik

- Tüm endpoint'ler `x-api-key` header doğrulaması gerektirir
- CORS yalnızca `NEXMEET_URL` değişkeninde tanımlı origin'e izin verir
- Ses dosyaları işlendikten sonra `/tmp` dizininden otomatik silinir
- Toplantı kayıtları indirildikten sonra diskten silinir
- `.env` dosyası asla git'e push edilmemelidir

---

## 🗂️ İlgili Repolar

| Repo | Açıklama |
|------|----------|
| [nexmeet](https://github.com/SHapeloglu/nexmeet) | NexMeet backend + frontend |
| [nexmeet-kokoro-tts-service](https://github.com/SHapeloglu/nexmeet-kokoro-tts-service) | Bu repo — TTS servisi |

---

## 📋 Servis Yönetimi

```bash
# Başlat
sudo systemctl start kokoro-tts.service

# Durdur
sudo systemctl stop kokoro-tts.service

# Yeniden başlat
sudo systemctl restart kokoro-tts.service

# Logları izle
sudo journalctl -u kokoro-tts.service -f

# Servis durumu
sudo systemctl status kokoro-tts.service
```

---

## 🏷️ Lisans

Bu proje NexMeet ekibine aittir. İzinsiz kullanım ve dağıtım yasaktır.
