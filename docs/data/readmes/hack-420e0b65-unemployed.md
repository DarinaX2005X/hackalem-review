# Alem Minutes — on-premise meeting protocol for Russian, Kazakh and mixed speech

HackAlem AI 2026, team **Unemployed**.

Upload a meeting recording, and the machine you are sitting at does everything:
speech recognition, speaker diarization, action-item extraction and the final
protocol document. In the default **Local Whisper (offline/private)** mode **no audio
and no text ever leave the host**: no cloud API, no account, no API key, no telemetry.

An optional, explicitly selected **Gemini (best RU/KZ accuracy)** transcription backend
sends the *audio* to Google's Gemini API (cloud) and needs `GEMINI_API_KEY`; see
[§3a](#3a-optional-cloud-transcription-gemini). In that mode the application is **not**
offline. Summary and action items are still extracted by the local Ollama model.

---

## 1. What the solution does

1. You upload an audio file (WAV, MP3/MPEG, M4A, OGG, FLAC, MP4, up to 200 MB).
2. **faster-whisper** (Whisper `large-v3`, CTranslate2) transcribes it with word
   timestamps. Voiced passages are decoded separately so a Russian passage cannot
   suppress a following Kazakh passage.
3. **sherpa-onnx** (pyannote segmentation 3.0 + 3D-Speaker embeddings, ONNX, CPU)
   finds speaker turns; every word is attributed to the speaker whose turn overlaps
   it most, and Whisper segments are split where the speaker changes mid-sentence.
4. You map the anonymous `SPEAKER_00…` voice clusters to real participant names.
5. A **local Ollama** model (`qwen3:4b-instruct-2507-q4_K_M`) produces a summary and
   structured action items — *responsible person*, *task*, *deadline*, *status* —
   each one carrying the transcript segment IDs and a verbatim supporting quote.
6. You review and edit the action table, then export the protocol as **DOCX**,
   **PDF** (with correct Cyrillic and Kazakh glyphs), plain transcript or JSON.

### Case requirements → implementation → verification

| # | Case requirement | Implemented in | Verify with | Expected observable result |
| --- | --- | --- | --- | --- |
| 1 | Speech-to-text | `minutes/transcription.py` | `uv run python scripts/smoke.py assets/demo/planning-ru-kk.wav --model large-v3 --diarize` | `STT: N segments; device=…; language=…` and a timestamped transcript in the JSON output |
| 2 | Russian speech | same, `language="ru"` or auto | `… --language ru` on a Russian recording | Russian text in `transcript.segments[].text` |
| 3 | Kazakh speech | same, `language="kk"` or auto | `… --language kk` on a Kazakh recording | Kazakh text, including `ә ғ қ ң ө ұ ү h і` |
| 4 | Mixed Russian/Kazakh | per-passage decoding + `multilingual=True` | `… ` with **no** `--language` on the demo file | `language=ru+kk`; Russian and Kazakh segments in one transcript |
| 5 | Action items with responsible + task + deadline | `minutes/extraction.py`, `ActionItem` in `minutes/models.py` | `uv run python scripts/verify_extraction.py` | 7 `PASS` lines (RU/KZ/mixed explicit date `2026-09-25`; “в понедельник” → `2026-09-28`, “в среду” → `2026-09-30`, “на следующей неделе” → `2026-10-02`, “жұмаға дейін” → `2026-09-25`, meeting date Wed `2026-09-23`): one action each, person `Айгүл`, speaker link, verbatim quote |
| 6 | Speaker diarization linked to people | `minutes/diarization.py` + “Who is speaking?” form in `app.py` | `… --diarize`, then map names in the UI | `Diarization: N turns, M speakers`; mapped names replace labels in transcript, actions and exports |
| 7 | Export protocol to PDF/DOCX | `minutes/exports.py` | `uv run pytest -q tests/test_exports.py` and the export buttons | `.docx`/`.pdf` containing summary, action table, evidence and transcript |
| — | Fully local / on-premise (Local Whisper mode) | `minutes/config.py` (loopback-only), isolated workers, `local_files_only=True` | `uv run pytest -q tests/test_core.py tests/test_extraction.py` | External URLs, proxies, redirects and remote/cloud Ollama models are rejected before any meeting text is sent |

---

## 2. Architecture

```
            ┌──────────────────────── this machine ────────────────────────┐
            │                                                              │
 browser ──▶│ Streamlit app.py ──▶ temp file (deleted after processing)     │
 (localhost)│        │                                                     │
            │        ├──▶ subprocess: faster-whisper  (CUDA → CPU fallback) │
            │        │        └── models/whisper/large-v3   (local files)   │
            │        │                                                      │
            │        ├──▶ subprocess: sherpa-onnx diarization (CPU ONNX)     │
            │        │        └── models/diarization/*.onnx (local files)    │
            │        │                                                      │
            │        ├──▶ word/turn overlap → Transcript(speaker per segment)│
            │        │                                                      │
            │        ├──▶ http://127.0.0.1:11434  Ollama (loopback only)     │
            │        │        └── schema-constrained JSON → Extraction       │
            │        │             + evidence validation + bounded repair    │
            │        │                                                      │
            │        └──▶ exports.py → DOCX / PDF / TXT / JSON (in memory)   │
            └──────────────────────────────────────────────────────────────┘
      no outbound network calls at runtime in Local Whisper mode (the default);
      the optional Gemini backend sends audio to generativelanguage.googleapis.com
```

| File | Responsibility |
| --- | --- |
| `minutes/models.py` | Pydantic contracts: `Word`, `Segment`, `Transcript`, `SpeakerTurn`, `ActionItem`, `Extraction`, `Meeting` |
| `minutes/config.py` | Settings from environment; rejects any non-loopback Ollama URL |
| `minutes/transcription.py` | Isolated Whisper worker, CUDA→CPU fallback, per-passage decoding, audio-decode errors |
| `minutes/diarization.py` | Isolated sherpa-onnx worker and timestamp-overlap speaker attribution |
| `minutes/extraction.py` | Local-model boundary, JSON-schema output, malformed-output recovery, evidence validation, chunking |
| `minutes/gemini.py` | Optional cloud Gemini transcription (explicit opt-in), response parsing to `Transcript` |
| `minutes/deadlines.py` | Deterministic RU/KZ relative-deadline resolution from the meeting date |
| `minutes/review.py` | Validated human edits of the action table |
| `minutes/exports.py` | DOCX and Unicode PDF generation with bundled fonts |
| `app.py` | Streamlit UI: upload → transcribe → name speakers → extract → review → export |
| `scripts/` | Pinned model downloads, real-inference smoke test, extraction check, demo-audio generator |

Whisper runs in a **separate process** so its GPU memory is released before Ollama
loads, which matters on an 8 GB laptop GPU, and so a native CUDA library crash
cannot take down the UI.

---

## 3a. Optional cloud transcription (Gemini)

Why: on real human RU/KZ recordings, local Whisper was noticeably weaker than Gemini,
especially for Kazakh and code-switching. Local mode stays the default and fully works
without Gemini.

Setup (only if you want this mode):

```bash
cp .env.example .env          # if you have no .env yet; .env is git-ignored
# edit .env and set your own key from https://aistudio.google.com/apikey :
# GEMINI_API_KEY=<your key>
# GEMINI_MODEL=gemini-3.5-flash   # optional, this is the default
```

Then restart Streamlit and choose **Gemini (best RU/KZ accuracy)** under
*Transcription backend* in the sidebar. The button changes to
**1. Transcribe with Gemini (cloud)** and a cloud warning is shown.

How it works (`minutes/gemini.py`): the upload is decoded locally to 16 kHz mono WAV and
sent via the official Gemini REST API (`generateContent`, inline for ≤14 MB, otherwise the
Files API, and the uploaded file is deleted afterwards). Gemini is instructed to transcribe
verbatim without translating or summarising, keep RU/KZ code-switching, and return JSON
segments with speaker and start/end seconds. They are converted into the same
`Transcript`/`Segment` structure (`Speaker 1` → `SPEAKER_00`, …), so speaker naming,
extraction, deadlines, review and DOCX/PDF/JSON exports are unchanged. Local ONNX
diarization is not applied in this mode. Timestamps are kept only if they are coherent
(ordered, inside the recording); otherwise they are shown as 00:00:00 with a warning
rather than invented. 429/5xx responses are retried twice. If the default
`gemini-3.5-flash` still answers **503 UNAVAILABLE / high demand**, the same audio is sent
once to `gemini-3.1-flash-lite`; the transcript then shows `Model: gemini-3.1-flash-lite`
and a warning naming the fallback. There is no fallback for auth, bad-request, quota (429)
or safety errors, and none when you set `GEMINI_MODEL` yourself (your choice is kept). Missing key, API errors and
network failures are shown as clean messages; the key is sent only in the
`x-goog-api-key` header and never logged or shown.

Privacy trade-off: **Gemini mode = the recording goes to Google** under your API key's
terms. Use Local Whisper for confidential meetings.

`gemini-3.5-transcribe` was tried first and rejected: it does not support JSON mode, returned
no speakers/timestamps, and dropped the Kazakh lines of the demo recording.

## 3. On-premise / privacy design (Local Whisper mode)

* **Loopback-only LLM.** `minutes/config.py::local_ollama_url` accepts only
  `http://127.0.0.1`, `http://localhost` or `http://[::1]` with no path, query,
  credentials or fragment, and resolves the host itself so DNS or proxy settings
  cannot redirect meeting text. The HTTP client runs with `trust_env=False`
  (ignores `HTTP(S)_PROXY`) and `follow_redirects=False`.
* **No remote model behind a local port.** Before any transcript is sent, the app
  calls `/api/show` and refuses models that report `remote_host` / `remote_model`,
  or whose name contains `cloud`.
* **No runtime downloads.** Whisper loads with `local_files_only=True` and
  `HF_HUB_OFFLINE=1`. Every model is fetched once by an explicit setup command.
* **Telemetry off.** Streamlit usage stats disabled in `.streamlit/config.toml`;
  ONNX Runtime telemetry disabled in both workers; HF telemetry disabled.
* **Data lifetime.** Uploaded audio is written to a temporary directory that is
  deleted as soon as processing finishes. Results live in the Streamlit session
  until you press *Clear meeting from session*. Only files you download persist.
* **Prompt-injection stance.** The transcript is passed to the model as untrusted
  data, and every extracted action must cite real segment IDs and a quote that
  actually occurs in the cited segment, or it is rejected and repaired.

The app binds to `127.0.0.1` and has **no authentication**. A shared internal
deployment needs an authenticated reverse proxy. For an air-gapped install,
pre-download the models and block outbound traffic, including from Ollama.

---

## 4. Requirements

* Linux or WSL2 (developed and verified on Ubuntu under WSL2, kernel 6.18).
* [`uv`](https://docs.astral.sh/uv/) — provides and pins CPython 3.12.
* [Ollama](https://ollama.com/) running locally.
* Disk: ~3.1 GB Whisper `large-v3`, ~51 MB diarization models, ~2.5 GB Ollama model,
  plus ~260 MB only if you generate the demo audio.
* RAM: 8 GB minimum for CPU inference; 16 GB comfortable.
* GPU is **optional**. An NVIDIA GPU with ≥6 GB VRAM speeds up transcription;
  everything falls back to CPU automatically.
* No ffmpeg binary needed — PyAV ships its own decoders.

---

## 5. Install

```bash
git clone <this repository>
cd hack-420e0b65-unemployed

# GPU (NVIDIA CUDA 12) — installs cuBLAS + cuDNN 9 wheels
uv sync --python 3.12 --extra gpu

# CPU-only machines
# uv sync --python 3.12

cp .env.example .env
```

## 6. Download the models (once, explicit)

```bash
ollama serve &                                   # if not already running
ollama pull qwen3:4b-instruct-2507-q4_K_M        # ~2.5 GB

uv run python scripts/download_models.py --whisper large-v3 --diarization
```

Every download is pinned: Whisper by upstream commit revision + per-file SHA-256,
the diarization archives by SHA-256. Re-running the command is a no-op once the
checksums match.

Lower-memory alternatives: `--whisper medium` (~1.5 GB) or `--whisper small`.
`--whisper tiny` is a pipeline smoke test only — it is **not** a Kazakh-quality
baseline. Select the matching model in the sidebar.

Optional demo voices (only needed to regenerate `assets/demo/planning-ru-kk.wav`):

```bash
uv run python scripts/download_models.py --demo-voices   # ~260 MB
uv run python scripts/make_demo_audio.py
```

## 7. Launch

```bash
uv run streamlit run app.py
```

Open <http://127.0.0.1:8501>.

---

## 8. Main demo workflow

A ready-made demo recording is committed at **`assets/demo/planning-ru-kk.wav`** —
a short synthetic planning meeting with three voices, Russian lines, Kazakh lines
and one code-switched Russian/Kazakh line containing explicit commitments.

1. Leave the sidebar defaults (`large-v3`, device `auto`, language
   *Auto / mixed RU + KZ*, diarization on, automatic extraction on).
2. Upload `assets/demo/planning-ru-kk.wav`, set the meeting date to `2026-09-23`.
3. Press **1. Transcribe locally**. Transcription, diarization and — with the
   default *Extract minutes automatically* option — the local LLM all run in one
   click. Progress is shown; the reported device is the device actually used.
4. Inspect the **timestamped transcript**: Russian and Kazakh segments, each with
   a `SPEAKER_xx` label. Open **Speaker timeline** to see the raw turns.
5. In **Who is speaking?**, type participant names for the labels and press
   *Apply participant names*. Names replace labels everywhere. (Changing the
   mapping clears previously generated minutes so they can be regenerated.)
6. Press **2. Extract summary and action items** (again, if you renamed speakers).
   Review the summary and the action table: responsible person, task, deadline,
   status, the verbatim evidence quote and its segment IDs.
7. Open **Review actions and update progress** to correct people, tasks and
   deadlines or mark tasks completed. *Overdue* is computed from the deadline.
8. Press **Download DOCX** / **Download PDF** for the protocol, or download the
   transcript or the full JSON.

### Where to put your own or the official case audio

Anywhere readable — you upload it through the browser. For command-line runs,
the convention used by this repository is:

```bash
mkdir -p artifacts            # already git-ignored
cp /path/to/case-meeting.m4a artifacts/
uv run python scripts/smoke.py artifacts/case-meeting.m4a \
    --model large-v3 --diarize --output artifacts/case-meeting.json
```

This writes `artifacts/case-meeting.json`, `.docx` and `.pdf` using exactly the
same code path as the UI. `artifacts/` and `models/` are git-ignored, so no
meeting material is ever committed.

---

## 9. Verification commands

```bash
uv run pytest -q                      # unit + UI + export + robustness tests
uv run ruff check .                   # lint
uv run python scripts/verify_extraction.py   # real local LLM: RU / KZ / mixed commitments
uv run python scripts/smoke.py assets/demo/planning-ru-kk.wav \
    --model large-v3 --diarize --output artifacts/demo.json   # full local pipeline
```

`scripts/verify_extraction.py` and `scripts/smoke.py` perform **real local
inference** — they need Ollama running and the models downloaded. They assert on
live model output; nothing is hardcoded or replayed.

Results actually observed on the development machine are recorded in
[`docs/VERIFICATION.md`](docs/VERIFICATION.md), including the cases where model
quality was imperfect.

---

## 10. CPU / GPU fallback

| Situation | Behaviour |
| --- | --- |
| `WHISPER_DEVICE=auto` (default) and CUDA works | Whisper runs on the GPU with `int8_float16` |
| CUDA missing, cuDNN broken, or the native process crashes | The isolated worker is retried on CPU with `int8`, and the UI shows *“CUDA transcription failed; automatically retried on CPU (int8).”* |
| `WHISPER_DEVICE=cpu` | CPU only, no GPU attempt |
| Diarization | Always CPU ONNX — no GPU required |
| Ollama | Uses whatever backend Ollama itself is configured with |

The device actually used is displayed under the transcript and stored in the
exported JSON, so a fallback is never silent.

---

## 11. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `Whisper model missing or incomplete: models/whisper/large-v3` | The model was not downloaded. Run `uv run python scripts/download_models.py --whisper large-v3`. |
| `Diarization models missing` warning, transcript still produced | Run `uv run python scripts/download_models.py --diarization`. Diarization failures never destroy a transcript. |
| `Local Ollama unavailable: … Connection refused` | Start `ollama serve`, then `ollama pull qwen3:4b-instruct-2507-q4_K_M`. Use the sidebar **Check local Ollama** button. |
| `OLLAMA_URL must be a local loopback HTTP address` | `.env` points at a non-local host. Only `127.0.0.1`, `localhost` or `[::1]` are allowed by design. |
| `This Ollama model delegates inference remotely and is forbidden` | The selected Ollama model is a cloud/remote model. Pull a local one. |
| `WHISPER_DEVICE must be one of auto, cuda, cpu` | Fix the value in `.env`. |
| `This file could not be decoded as audio` | The upload is not a readable media file. Re-export it as WAV or MP3. |
| Transcription falls back to CPU on every run | CUDA libraries are unavailable. Install with `--extra gpu`, or accept CPU (slower but identical output format). |
| `Ollama returned invalid minutes after 3 attempts` | The local model failed to produce valid JSON three times. The transcript is preserved — press **2. Extract…** again, or use a stronger local model via `OLLAMA_MODEL`. |
| Out of GPU memory | Choose `medium`/`small` in the sidebar, or set `WHISPER_DEVICE=cpu`. Whisper already exits before Ollama loads. |
| Speakers merged or split | Set **Known number of speakers** in the sidebar to the real count and transcribe again. |
| PDF shows boxes instead of letters | Should not happen — fonts are bundled in `assets/fonts/`. Verify the files exist. |

---

## 12. Environment variables

All values are optional; defaults work. The only secret is the optional
`GEMINI_API_KEY` (Gemini mode only). See [`.env.example`](.env.example).

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Loopback Ollama endpoint; non-local values are rejected |
| `OLLAMA_MODEL` | `qwen3:4b-instruct-2507-q4_K_M` | Locally pulled Ollama model |
| `WHISPER_MODEL` | `large-v3` | Default Whisper model directory under `MODEL_DIR/whisper/` |
| `WHISPER_DEVICE` | `auto` | `auto`, `cuda` or `cpu` |
| `MODEL_DIR` | `models` | Root of downloaded model files |
| `GEMINI_API_KEY` | *(empty)* | Only for the optional cloud Gemini backend; keep it in `.env` (git-ignored) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Gemini model used by the cloud backend; setting it disables the automatic 503 fallback to `gemini-3.1-flash-lite` |

---

## 13. Known limitations

* **Gemini mode is cloud processing** and depends on Google's availability: during
  testing `gemini-3.5-flash` intermittently returned `503 high demand` even after retries.
  Gemini speaker labels and timestamps are model estimates. Gemini may write numbers as
  words (“к двадцать пятому сентября”). Very long recordings can exceed the output limit
  (reported as “truncated”).

* **Recognition quality is not perfect**, especially for Kazakh. A measured example
  is recorded in `docs/VERIFICATION.md` (“Әлемнің жұлдыздары” → “Әлімнің
  жолдыздары”). Always review the transcript against the audio.
* Schema validation and verbatim-quote checks prove *provenance*, not semantic
  correctness. Extracted minutes are an **AI draft for human review**, and the UI
  and both export formats say so.
* Long meetings are chunked (~6500 characters per request) and the per-chunk
  summaries are concatenated; a commitment split across a chunk boundary may lose
  context. The stored summary is capped at 6000 characters.
* Diarization can merge similar voices or split one speaker; equally overlapping
  voices are deliberately left `UNKNOWN` rather than guessed. Words in a short
  pause (≤0.3 s) between turns join the nearer turn. A task is linked to a speaker
  only if that speaker voiced a cited evidence segment; otherwise the speaker link
  is dropped (an explicitly named assignee is kept). Speaker labels are
  voice clusters — the human mapping step is what links them to real people.
* Relative deadlines are resolved **in code** (`minutes/deadlines.py`) from the
  meeting date you enter: weekdays (“в понедельник”, “до пятницы”, “жұмаға дейін”;
  the same weekday as the meeting means next week), “в следующий …”, “завтра /
  ертең”, “послезавтра”, “через неделю”. A range such as “на следующей неделе /
  келесі аптада” is set to the **Friday** of that week (the spoken words stay in
  the deadline text). Other wording (e.g. “в конце месяца”) is left to the LLM,
  which is told to return no date when unsure; verify deadlines in review.
* Session state only. There is no database, no multi-user support, no
  authentication and no task-tracker integration — export DOCX/PDF/JSON to keep
  results.
* Maximum upload 200 MB and maximum recording length 2 hours.
* The demo recording is **synthetic TTS speech**, not a real meeting; it exercises
  the pipeline, it does not benchmark accuracy on real human recordings.

---

## 14. Roadmap: Teams / Zoom / SED integration

Not implemented — listed here as the designed extension path, and deliberately not
claimed as working functionality.

* **Ingestion adapters.** `minutes/transcription.py` already takes a plain audio
  path, so a Teams/Zoom/Google Meet adapter only needs to drop the meeting
  recording into the same call. On-prem recording bots (e.g. an SIP/RTP recorder,
  or the Zoom local-recording folder) keep the audio inside the perimeter.
* **Near-real-time mode.** The per-passage VAD loop in `worker()` is already
  chunked; feeding it a rolling buffer would give live captions without design
  changes.
* **SED / EDMS (СЭД) export.** `Meeting.model_dump_json()` is a stable typed
  contract with responsible person, task, deadline, status and evidence. A thin
  connector can post those fields into Directum/ELMA/1C-Document Flow or create
  issues in Jira/Planner, attaching the generated DOCX/PDF as the protocol.
* **Identity linking.** Replace the manual name mapping with speaker enrolment:
  the same 3D-Speaker embedding model can match a voice against a stored
  per-employee embedding, turning `SPEAKER_00` into a directory identity.
* **Multi-user deployment.** Put the app behind an authenticated gateway, move
  session state into a database, and keep per-meeting access control.

---

## 15. Third-party components and licenses

Team work: pipeline design and integration, UI, validation logic, prompts, tests,
verification and documentation. Everything below is third-party material used under
its own license. Exact dependency versions are pinned in `uv.lock`.

| Component | Source | License |
| --- | --- | --- |
| faster-whisper / CTranslate2 | [SYSTRAN](https://github.com/SYSTRAN/faster-whisper) / [OpenNMT](https://github.com/OpenNMT/CTranslate2) | MIT |
| Whisper `large-v3` converted weights | [OpenAI Whisper](https://github.com/openai/whisper) / [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | MIT |
| Qwen3-4B-Instruct-2507 (via Ollama) | [Qwen](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | Apache-2.0 |
| Ollama | [ollama/ollama](https://github.com/ollama/ollama) | MIT |
| Streamlit | [streamlit](https://github.com/streamlit/streamlit) | Apache-2.0 |
| Pydantic / HTTPX / python-dotenv | [Pydantic](https://github.com/pydantic/pydantic) / [HTTPX](https://github.com/encode/httpx) / [dotenv](https://github.com/theskumar/python-dotenv) | MIT / BSD-3-Clause / BSD-3-Clause |
| PyAV (bundled FFmpeg decoders) | [PyAV](https://github.com/PyAV-Org/PyAV) | BSD-3-Clause; bundled FFmpeg under its LGPL/GPL terms |
| sherpa-onnx + native runtime | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | Apache-2.0 |
| pyannote segmentation 3.0 (ONNX export) | [sherpa-onnx release](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speaker-segmentation-models) | MIT (CNRS); LICENSE copied to `models/diarization/SEGMENTATION-LICENSE` |
| 3D-Speaker ERes2Net speaker embedding | [3D-Speaker](https://github.com/modelscope/3D-Speaker) / [ONNX release](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speaker-recongition-models) | Apache-2.0 |
| python-docx / ReportLab | [python-docx](https://github.com/python-openxml/python-docx) / [ReportLab](https://www.reportlab.com/) | MIT / BSD |
| DejaVu Sans fonts (bundled, for PDF) | [DejaVu Fonts](https://dejavu-fonts.github.io/) | Bitstream Vera + DejaVu terms, see `assets/fonts/LICENSE.txt` |
| Piper VITS voices `ru_RU-denis`, `ru_RU-irina`, `kk_KZ-issai` (demo audio only) | [Piper](https://github.com/rhasspy/piper) / [sherpa-onnx tts-models](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models); Kazakh voice from [ISSAI](https://issai.nu.edu.kz/) | MIT (Piper); voice model terms per upstream release |
| NVIDIA cuBLAS / cuDNN wheels (optional GPU extra) | [NVIDIA](https://docs.nvidia.com/cuda/) | NVIDIA redistribution terms |

Respect these licenses when redistributing the application or the downloaded model
artifacts. See [`docs/BRIEF.md`](docs/BRIEF.md) for the requirement/scoring map and
[`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the verification log.
