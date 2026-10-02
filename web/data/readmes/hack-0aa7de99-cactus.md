# Cactus — local meeting protocol (Track 8)

This is the team's local Track 8 app. It has been run on an Apple Silicon Mac with macOS and Python 3.12. Use an Apple Silicon Mac with enough memory and disk for the local models; Intel Macs and other platforms have not been tested. Install FFmpeg (including `ffprobe`) and have `curl` and `tar` available. The first setup needs internet access to install dependencies and download models. Processing uses local models; meeting audio and transcripts stay on the Mac.

## One-time setup

From a clone of this repository:

```bash
cd ~/Downloads/track8
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p models/whisper models/diarization models/ollama-runtime
.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="mlx-community/whisper-large-v3-turbo-q4",
    revision="660c343bbf4e52ac257f0b7d952e5388e6f93bef",
    local_dir="models/whisper",
)
snapshot_download(
    repo_id="pyannote-community/speaker-diarization-community-1",
    revision="8a527374977391da736e0daaef26855d949d9685",
    local_dir="models/diarization",
)
PY
curl -fL https://github.com/ollama/ollama/releases/download/v0.34.3/ollama-darwin.tgz -o /private/tmp/track8-ollama.tgz
tar -xzf /private/tmp/track8-ollama.tgz -C models/ollama-runtime
```

Start Ollama in one terminal, from the repository root:

```bash
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 \
OLLAMA_MODELS="$PWD/models/ollama" models/ollama-runtime/ollama serve
```

In another terminal, download the extraction model once:

```bash
cd ~/Downloads/track8
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_MODELS="$PWD/models/ollama" \
models/ollama-runtime/ollama pull qwen2.5:7b
```

## Launch and export a protocol

Keep Ollama running. In the second terminal:

```bash
cd ~/Downloads/track8
export ASR_MODEL="$PWD/models/whisper"
export DIARIZATION_MODEL="$PWD/models/diarization"
export OLLAMA_MODEL=qwen2.5:7b
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open <http://127.0.0.1:8501>. Upload a local MP3, WAV, or M4A recording. Click **“1. Распознать запись / принять транскрипт”**; correct speaker labels if needed. Click **“2. Извлечь поручения локально”**, review or edit the actions, then click **“Скачать протокол DOCX”**. The browser downloads the generated document; do not commit recordings, transcripts, or generated protocols. For batch processing and local output checks, see [`LOCAL_RUN.md`](LOCAL_RUN.md).
