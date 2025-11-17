# Skryba

Multilingual media scribing, translation, and summarization pipeline with GPU acceleration. Skryba ingests audio/video (file or URL), transcribes speech, groups subtitles intelligently, normalizes to a standard language, summarizes with a long‑context model, and optionally re‑translates the summary into any supported target language. Outputs include grouped SRT captions, raw summary (`summary_en.md`), and translated summary (`summary_<lang>.md`).

Includes a modern React web interface with drag-and-drop upload and real-time processing feedback.

Future roadmap adds: a music‑to‑notes (MIDI/score) converter module.

---
## ✨ Features

- **Web UI**: Modern React interface with drag-and-drop file upload and URL input
- Speech transcription (Whisper large‑v3) with batched GPU inference
- Automatic source language detection and MBART‑50 code mapping
- Normalization pass (translate everything to a pivot language, default English)
- Subtitle grouping (configurable chunk size) for better summarization context
- Long‑context summarization (Granite 3.3 2B Notetaker) with very high max tokens
- Line‑aware summary translation preserving blank lines & Markdown semantics
- Markdown post‑processing (fixes bold spacing, bullet formatting)
- TF32 acceleration for Ampere+ NVIDIA GPUs
- Zip packaging of all generated artifacts per request
- Clean ephemeral storage with background cleanup

---
## 🧱 Architecture

```
Browser → Frontend (React Router) → API Gateway (FastAPI) → Scribe Service (FastAPI)
              ↓                            |                          |
         Port 3000                    Port 8000                  Port 8001
                                           |                          |
                                           |                          ├─ Whisper transcription
                                           |                          ├─ Language detection (XLM-R)
                                           |                          ├─ MBART translation (pivot + target)
                                           |                          ├─ Subtitle grouping (SRT parser)
                                           |                          ├─ Summarization (Granite model)
                                           |                          └─ Markdown cleanup & packaging
                                           |
                                      PostgreSQL ←(metadata: file ids, lifecycle)→ Scribe Service
```

Components:
- `frontend/`: React Router web interface with file upload, URL input, and language selection.
- `api-gateway/`: Thin proxy layer forwarding file/URL requests to scribe service.
- `scribe-service/`: Core processing pipeline and storage lifecycle.
- `compose.yaml`: Multi‑service orchestration (GPU reservation, volumes, DB).

---
## 🚀 Quick Start (Docker Compose)

Prerequisites:
- Docker + Docker Compose
- NVIDIA Container Toolkit (for GPU acceleration) if using CUDA devices

PowerShell (Windows):
```powershell
git clone https://github.com/Virtover/skryba.git
cd skryba
docker compose build
docker compose up -d
```

Access the application:
- **Web UI**: `http://localhost:3000` (recommended - modern interface)
- **API Gateway**: `http://localhost:8000` (direct API access)

---
## 🎨 Using the Web Interface

1. Open `http://localhost:3000` in your browser
2. Choose your input method:
   - **📁 Upload File**: Drag & drop or click to select audio/video files
   - **🔗 From URL**: Paste a direct link to media content
3. Select your desired summary language (50+ languages supported)
4. Click **🚀 Transcribe & Summarize**
5. Wait for processing (progress indicator shown)
6. Your results will automatically download as a ZIP file containing:
   - `out.srt` - Original transcription with timestamps
   - `out_grouped.srt` - Grouped subtitles for better readability
   - `summary_en.md` - English summary
   - `summary_<lang>.md` - Translated summary (if requested language differs from English)

---
## 🔧 Configuration

Environment variables (set in `compose.yaml` for `scribe-service`):

| Variable | Purpose | Example |
|----------|---------|---------|
| POSTGRES_HOST | DB host:port | `scribe-db:5432` |
| POSTGRES_USER | DB username | `scribe` |
| POSTGRES_PASSWORD | DB password | `password` |
| POSTGRES_DB | DB name | `database` |
| DEVICE | Inference device selector (`cpu`, `cuda`, `insane`) | `insane` |
| HF_TOKEN | Hugging Face token (optional) | `hf_xxx` |

Frontend configuration (set in `compose.yaml` build args):
| Variable | Purpose | Example |
|----------|---------|---------|
| VITE_API_URL | API Gateway URL | `http://localhost:8000` |

`DEVICE=insane` is a project‑specific shortcut (maps internally to an accelerated setting). Fallbacks to CPU when GPU not present.

TF32 is enabled automatically for supported GPUs.

---
## 🌐 Language Support

### Input language detection & transcription (subset)
arabic (ar), bulgarian (bg), german (de), modern greek (el), english (en), spanish (es), french (fr), hindi (hi), italian (it), japanese (ja), dutch (nl), polish (pl), portuguese (pt), russian (ru), swahili (sw), thai (th), turkish (tr), urdu (ur), vietnamese (vi), chinese (zh)

### Summary translation targets (MBART‑50 codes)
Arabic (ar_AR), Czech (cs_CZ), German (de_DE), English (en_XX), Spanish (es_XX), Estonian (et_EE), Finnish (fi_FI), French (fr_XX), Gujarati (gu_IN), Hindi (hi_IN), Italian (it_IT), Japanese (ja_XX), Kazakh (kk_KZ), Korean (ko_KR), Lithuanian (lt_LT), Latvian (lv_LV), Burmese (my_MM), Nepali (ne_NP), Dutch (nl_XX), Romanian (ro_RO), Russian (ru_RU), Sinhala (si_LK), Turkish (tr_TR), Vietnamese (vi_VN), Chinese (zh_CN), Afrikaans (af_ZA), Azerbaijani (az_AZ), Bengali (bn_IN), Persian (fa_IR), Hebrew (he_IL), Croatian (hr_HR), Indonesian (id_ID), Georgian (ka_GE), Khmer (km_KH), Macedonian (mk_MK), Malayalam (ml_IN), Mongolian (mn_MN), Marathi (mr_IN), Polish (pl_PL), Pashto (ps_AF), Portuguese (pt_XX), Swedish (sv_SE), Swahili (sw_KE), Tamil (ta_IN), Telugu (te_IN), Thai (th_TH), Tagalog (tl_XX), Ukrainian (uk_UA), Urdu (ur_PK), Xhosa (xh_ZA), Galician (gl_ES), Slovene (sl_SI)

---
## 📡 API Usage

> **Note**: For most users, the web interface at `http://localhost:3000` is recommended. The API endpoints below are for direct programmatic access.

### 1. Scribe from file
POST `/scribe-file/{summary_lang}`

Multipart form field: `file` (audio/video)

Response: ZIP archive containing:
- `out.srt` (original transcription)
- `out_grouped.srt` (grouped subtitles)
- `summary_en.md` (pivot summary)
- `summary_<summary_lang>.md` (if translation requested and differs from English)

Example (PowerShell):
```powershell
Invoke-WebRequest -Uri http://localhost:8000/scribe-file/pl_PL -Method POST -InFile .\sample.mp3 -OutFile result.zip -ContentType multipart/form-data
```

### 2. Scribe from URL
POST `/scribe-url/{summary_lang}`

JSON body:
```json
{ "url": "https://example.com/media.mp4" }
```
Same ZIP structure in response.

### Language codes
Use MBART‑50 target codes (e.g., `pl_PL`, `fr_XX`, `en_XX`). Source language auto‑detected.

---
## 🧪 Internal Processing Flow
1. Save input file or download from URL.
2. Transcribe with Whisper (batched, GPU if available).
3. Parse SRT and group entries (`group_size=20`).
4. Detect language of first chunk, map to MBART code.
5. Translate chunks to pivot language (`en_XX`).
6. Summarize merged text with long‑context model.
7. Clean summary markup and optionally translate to target language.
8. Write artifacts & create ZIP.
9. Queue background cleanup (DB rows + temp files).

---
## 🛣 Roadmap
- ✅ ~~Frontend UI (React/Vue + real‑time progress)~~ **COMPLETED**
- Music‑to‑notes converter (audio → MIDI/score using pitch detection + quantization)
- WebSocket support for real-time progress updates
- Persistent job queue & retry (Redis/RQ or Celery)
- User authentication and job history
- Observability: Prometheus metrics + OpenTelemetry traces
- Batch processing for multiple files

---
## 🩺 Troubleshooting
| Symptom | Possible Cause | Fix |
|---------|----------------|-----|
| Frontend not loading | Services not started | Run `docker compose up -d` and check logs with `docker compose logs frontend` |
| Empty ZIP | Unsupported media/container | Convert locally with `ffmpeg -i input.mp4 output.wav` |
| Slow summarization | GPU not utilized (note: on RTX 4050 laptop GPU, processing of 20-minute long audio took 20 minutes) | Check NVIDIA toolkit + `DEVICE` env var |
| Bold markdown malformed | Regex edge case | Report example; adjust `translate_summary()` cleanup rules |
| DB errors on startup | Stale volume state | Remove `scribe-db-data` volume and restart |
| CORS errors in browser | API URL misconfigured | Check `VITE_API_URL` in frontend build args |
| Empty ZIP | Unsupported media/container | Convert locally with `ffmpeg -i input.mp4 output.wav` |
| Slow summarization | GPU not utilized (note: on RTX 4050 laptop GPU, processing of 20-minute long audio takes 20 minutes) | Check NVIDIA toolkit + `DEVICE` env var |
| Bold markdown malformed | Regex edge case | Report example; adjust `translate_summary()` cleanup rules |
| DB errors on startup | Stale volume state | Remove `scribe-db-data` volume and restart |

Cleanup validation: service purges DB rows and directories after response; verify with `docker compose logs scribe-service`.

---
## 📄 License
See `LICENSE` (MIT unless otherwise specified).

---
## 🤝 Contributing
1. Fork & branch
2. Add tests or sample media for new features
3. Keep README and language tables in sync
4. Submit PR with concise description and performance notes

---
## 🧪 Dev Notes
- Set `HF_TOKEN` to `None` if you don't need gated models
- Adjust subtitle grouping in `scribe-service/app/utils.py` (`group_size`)
- Model swapping: update summarizer pipeline model id in `utils.py`
- Space normalization rules live in `translate_summary()`

---
## 📬 Contact
Open GitHub issues for bugs, feature requests, or language support additions.
