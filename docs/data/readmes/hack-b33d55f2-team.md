# Quryltai AI

A privacy-first local AI meeting protocol assistant for HackAlem. The planned application turns Russian, Kazakh, and mixed-language meetings into speaker-labeled transcripts, action items, summaries, and DOCX/PDF protocols.

## Final MVP status

The Streamlit application has three clearly separated paths:

- **Demo** is the original fictional, deterministic Russian/Kazakh example and works without Ollama.
- **Text transcript** analyzes pasted Russian, Kazakh, or mixed text using a locally running Ollama model. It produces grounded action items, source quotes, confidence scores, main topics, key problems, decisions, and an overall summary.
- **Audio (Phase 3)** transcribes WAV, MP3, or M4A locally with faster-whisper and sends the resulting text only to the same local Ollama pipeline.

DOCX and PDF downloads contain meeting metadata, participants, speaker mapping, action items, summary, and transcript. Uploaded audio is written only to an operating-system temporary file during transcription and is deleted immediately afterward. Speaker edits are reflected in displayed and exported results but are not persisted.

### MVP architecture

`src/llm/base.py` defines a provider interface. `src/llm/ollama.py` implements it with the Ollama HTTP API, schema-constrained output, Pydantic validation, and loopback-only URL enforcement. `src/understanding.py` turns pasted lines into evidence-addressable segments, sends one structured request to the local model, and rejects unknown evidence IDs, non-verbatim quotes, invented assignees, and invented deadline phrases before building a Protocol.

The provider boundary leaves room for another self-hosted runtime later without changing meeting analysis or the UI. There is no cloud provider implementation and no cloud fallback.

## Install (Windows PowerShell)

Use Python 3.11 or 3.12. The requirements include Streamlit, Pydantic, faster-whisper, python-docx, ReportLab, and pypdf. Installing them does not download an Ollama or Whisper model.

This checkout was verified with the already installed Python 3.13.15, Streamlit 1.64.0, and Pydantic 2.13.5. Its `.venv` is ready to run. A fresh installation can use the commands below.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If Python is installed as `python` instead of `py`, use `python -m venv .venv`. With uv already installed, an alternative is:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

## Configure Ollama locally

Install Ollama from https://ollama.com/download/windows. The recommended laptop model is `qwen3:4b-instruct-2507-q4_K_M`, a roughly **2.5 GB** Q4 model. It is small enough for a hackathon laptop and the Qwen3 family supports 100+ languages. This is a pragmatic starting point; evaluate Kazakh extraction on your own recordings. For a stronger machine, `qwen3:8b` is about 5.2 GB.

No model is downloaded by this repository. After installing Ollama, run these commands yourself:

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_NO_CLOUD', '1', 'User')
$env:OLLAMA_NO_CLOUD = '1'
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama list
```

Restart the Ollama application after setting the persistent environment variable. `OLLAMA_NO_CLOUD=1` disables Ollama cloud features. Quryltai additionally rejects non-loopback provider URLs.

Optional configuration must still point to loopback:

```powershell
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:QURYLTAI_OLLAMA_MODEL = 'qwen3:4b-instruct-2507-q4_K_M'
$env:QURYLTAI_OLLAMA_TIMEOUT_SECONDS = '300'
```

## Configure local audio transcription

Audio mode never downloads weights automatically. Point it at an existing local faster-whisper model folder:

```powershell
$env:QURYLTAI_WHISPER_MODEL_PATH = 'C:\HackAlemModels\faster-whisper-small'
```

If you do not already have local Whisper weights and choose to download them, run this once while online (the `small` multilingual model is several hundred MB):

```powershell
New-Item -ItemType Directory -Force C:\HackAlemModels | Out-Null
.\.venv\Scripts\hf.exe download Systran/faster-whisper-small --local-dir C:\HackAlemModels\faster-whisper-small
```

The current MVP transcribes speech but does not diarize multiple voices. Audio becomes neutral transcript segments; provide participant names as metadata and review the transcript before relying on assignments.

## Run

```powershell
$env:QURYLTAI_DATA_DIR = 'C:\HackAlemData'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:QURYLTAY_OLLAMA_MODEL = 'qwen3:4b-instruct-2507-q4_K_M'
$env:QURYLTAI_OLLAMA_TIMEOUT_SECONDS = '300'
# Required only for Audio mode:
$env:QURYLTAI_WHISPER_MODEL_PATH = 'C:\HackAlemModels\faster-whisper-small'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://127.0.0.1:8501. Leave **Demo mode** enabled for the offline deterministic demo. For real local understanding, turn Demo mode off, select **Text transcript**, paste the example below, and click **Analyze meeting**:

```text
Айгерім: Тимур, подготовь бюджет до пятницы.
Тимур: Жақсы, жұмаға дейін дайындаймын.
Дана: Ещё нужно проверить договор, бірақ жауапты адам әлі жоқ.
Айгерім: Шешім қабылданды: пилотты бес дүкенмен бастаймыз.
```

Use one utterance per line with `Name: text` or `[Name]: text`. Lines without a prefix use the neutral speaker label `Transcript`. Relative dates are resolved against the meeting date and `Asia/Qyzylorda` timezone when unambiguous. For audio, select **Audio (Phase 3)**, upload WAV/MP3/M4A, and analyze. After any successful mode, use the enabled **Export DOCX** and **Export PDF** download buttons.

The default fictional date is September 23, 2026. Participants are metadata, not automatic voice identification. Input changes apply when the form is submitted. The app preserves results through normal widget reruns; a new session/server restart loses them.

## Presentation demo checklist

1. Start Ollama and verify `ollama list` shows `qwen3:4b-instruct-2507-q4_K_M`.
2. Start Streamlit with the commands above.
3. Keep **Demo mode** on, select **Analyze meeting**, edit one speaker name, and download both protocol formats. This path needs neither Ollama nor Whisper.
4. Turn **Demo mode** off, keep **Text transcript**, paste the short sample above, and analyze it with local Ollama.
5. Optional audio demo: configure `QURYLTAI_WHISPER_MODEL_PATH`, select **Audio (Phase 3)**, upload a short clear WAV/MP3/M4A clip, and analyze it.

## Privacy and local storage

- Demo processing runs inside Streamlit. Text mode connects only to the configured loopback Ollama service. No meeting-data path to OpenAI or another external/cloud AI API exists in the application.
- Set `OLLAMA_NO_CLOUD=1`, restart Ollama, and preload the model before entering a closed environment. Runtime analysis then needs no internet connection.
- Streamlit binds to `127.0.0.1`, and usage statistics are disabled in `.streamlit/config.toml`. Run from the repository root so this configuration is loaded. Do not expose the development app through public tunnels or cloud hosting.
- Uploaded audio remains local. A temporary transcription copy is deleted immediately; meeting results remain in Streamlit session memory.
- The future data directory defaults to `C:\HackAlemData` on Windows (`~/HackAlemData` elsewhere). Override with `QURYLTAI_DATA_DIR` before launch. Phase 2 validates the location but **does not create it or write meeting files**.
- Repository paths, network shares, and known OneDrive locations are rejected. The user must verify the chosen directory is not synchronized by another backup/sync service. This repository itself may be in OneDrive; runtime meeting files must stay outside it.
- `.gitignore` excludes common audio, transcript, document, environment, model, and temporary file formats. It is a second guard, not a substitute for external storage; it does not protect already tracked files or forced Git additions.
- Package installation requires internet access unless using predownloaded packages. Runtime demo analysis can work offline. No database is used.

## Structure

```text
app.py                    Streamlit interface
src/config.py             External data path validation
src/schemas.py            Pydantic models and reference validation
src/demo.py               Fictional bilingual fixtures (safe source code)
src/orchestrator.py       Phase 1 deterministic demo workflow
src/understanding.py      Grounded text analysis and prompt
src/transcription.py      Local faster-whisper adapter
src/exporters.py          In-memory DOCX and PDF generation
src/llm/base.py           Local provider abstraction
src/llm/ollama.py         Loopback-only Ollama provider
.streamlit/config.toml    Loopback binding and telemetry opt-out
tests/test_foundation.py  Pipeline, schemas, privacy path checks
tests/test_app.py         Streamlit UI smoke checks
tests/test_understanding.py Structured-output and grounding checks
tests/test_exports.py     Audio adapter and real export checks
requirements.txt          Final MVP dependencies
```

## Component status

1. `normalize_audio`: handled internally by faster-whisper/PyAV for supported uploads.
2. `transcribe_audio`: implemented with faster-whisper and explicitly configured local weights.
3. `diarize_speakers`: not implemented in the MVP; audio uses a neutral speaker label.
4. `align_speakers`: not implemented because diarization is not included.
5. `extract_tasks`: implemented for pasted text with local Ollama, validation, and evidence references.
6. `generate_summary`: implemented for pasted text with local Ollama.
7. `generate_protocol`: implemented as validated in-memory DOCX and PDF exports using Unicode-capable local fonts.

The deterministic demo remains available without Ollama or Whisper. There is no external cloud AI fallback.

## Basic checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Checks use mocked providers and synthetic fixtures, require no model, make no network calls, and do not retain meeting files. Real transcription and extraction quality still depend on the selected local models and representative Russian/Kazakh recordings.
