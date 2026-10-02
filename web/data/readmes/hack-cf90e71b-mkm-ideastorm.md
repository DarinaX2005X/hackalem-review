# QazMeeting AI

On-premise meeting assistant for Russian, Kazakh, and mixed-language meetings. The existing dashboard, demo meeting, SQLite storage, meeting view, and DOCX/PDF exports remain available. Runtime audio and transcripts stay on the local machine; there is no OpenAI, cloud STT, or cloud LLM integration.

## Demo mode (zero model dependencies)

From the repository directory in Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DEMO_MODE = "true"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Demo mode is the default. It uses the existing Russian/Kazakh/mixed-language sample meeting and does not import or need faster-whisper or download any AI models. New meeting creation and exports continue to work as before. Demo data is stored locally in `data/qazmeeting.db`.

## Real local speech-to-text

Audio upload is enabled when `DEMO_MODE=false`. Install faster-whisper in the virtual environment; it is deliberately excluded from the lightweight demo requirements:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install faster-whisper
$env:DEMO_MODE = "false"
$env:WHISPER_MODEL = "small"
$env:WHISPER_DEVICE = "cpu"
$env:WHISPER_COMPUTE_TYPE = "int8"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The first model initialization requires the selected CTranslate2 model to be available in the local cache. faster-whisper may download the model weights on first use; prepare/cache the model while connected if the runtime machine is offline. No model download occurs during the demo setup or automated checks. The suggested development model is `small`; `WHISPER_MODEL` also accepts faster-whisper model names or a local model directory. The default language is automatic (`language=None`) so Russian, Kazakh, and code-switching are not forced into one language. Segment timestamps and detected language are saved with the recognized text.

Environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DEMO_MODE` | `true` | Select demo adapters or local transcription/upload |
| `WHISPER_MODEL` | `small` | faster-whisper model name or local model path |
| `WHISPER_DEVICE` | `cpu` | Inference device, such as `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | CTranslate2 compute type; `int8` is suitable for CPU |
| `DATABASE_PATH` | `data/qazmeeting.db` | Local SQLite database path |
| `UPLOAD_DIR` | `data/uploads` | Private local audio upload directory |

For GPU, install a compatible CUDA/cuDNN and CTranslate2 setup for your hardware, then set `WHISPER_DEVICE=cuda` and a supported compute type such as `float16`. CPU is the supported simple setup; GPU setup depends on the local driver/runtime.

Supported uploads: `.mp3`, `.wav`, `.m4a`, `.mp4` (maximum 1 GB). In local-AI mode click **New meeting / Upload recording**, enter a title, choose the recording, and select **Upload and transcribe locally**. The page reports progress during processing and opens the saved transcript when complete. Invalid formats and processing failures are reported in the UI.

## Privacy and storage

Inference runs through faster-whisper on this machine. Uploaded recordings are written to `data/uploads`; meeting text and timestamps are stored in the local SQLite database. These runtime files, `.env`, exports, and common model/cache directories are excluded from Git. Keep the host filesystem and any backups under your organization’s control. Avoid serving the app on an untrusted network; the current hackathon app does not implement user authentication.

## Current limitations

- Local transcription supports Russian and Kazakh through the multilingual Whisper model; mixed-language recognition quality depends on the model and audio.
- A transcript segment currently receives the temporary label **Speaker 1 (unverified)**. It is not a diarization result.
- Real speaker diarization is the **NEXT implementation step**. The transcription, diarization, and aligned-transcript domain structures are separated so a future local pyannote adapter can align speaker turns with Whisper segments.
- Summaries and action items are not generated from uploaded recordings in this iteration. The demo meeting retains its existing sample summary and action items.
- No real transcription confidence values are fabricated.

## Development checks

```powershell
python -m compileall app
```

This check does not install dependencies or download model files.
