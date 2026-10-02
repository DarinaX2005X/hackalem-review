# Meeting AI Assistant

Локальный прототип обработки записей совещаний.

## Запуск backend

Рекомендуется Python 3.11 или 3.12 и FFmpeg в PATH. Python 3.14 пока может быть несовместим с частью ML-зависимостей, поэтому для стабильной установки лучше использовать Python 3.12.

Portable-версию FFmpeg можно хранить прямо в проекте: распакуйте full-shared архив так, чтобы DLL находились в `backend/tools/ffmpeg/bin`. Backend автоматически добавит эту папку в PATH при запуске. При необходимости путь можно переопределить через `FFMPEG_DIR` в `.env`.

Для установки зависимостей:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

При первом запуске `faster-whisper` скачает выбранную модель. Для закрытого контура модель нужно заранее разместить в локальном кэше или подключить локальный путь к модели.

Диаризация выполняется локально через `pyannote.audio`. Для первоначального скачивания модели может потребоваться токен Hugging Face и принятие условий модели. В закрытом контуре модель скачивается заранее, после чего `DIARIZATION_MODEL` указывает на локальный каталог.

## API

Загрузить файл:

```powershell
curl.exe -X POST http://localhost:8000/meetings -F "file=@meeting.mp3"
```

Проверить статус и получить транскрипт:

```powershell
curl.exe http://localhost:8000/meetings/<meeting_id>
curl.exe http://localhost:8000/meetings/<meeting_id>/result
```

Поддерживаются `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`, `.mp4`, `.mov`, `.webm`, `.avi`. Результат содержит язык, временные метки, текстовые сегменты и назначенного говорящего.

Пример результата:

```json
{
  "language": "ru",
  "diarization": {"enabled": true, "speakers": ["SPEAKER_00", "SPEAKER_01"]},
  "segments": [
    {"start": 0.0, "end": 2.4, "text": "Добрый день", "speaker": "SPEAKER_00"}
  ]
}
```
