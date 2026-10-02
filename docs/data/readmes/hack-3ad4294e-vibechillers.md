# Function Lineage Auditor

Рабочее место для проверки изменений функций и подразделений между комплектами документов «До» и «После»: сопоставления, возможные потери/дублирование, потенциальные конфликты интересов, аналитическое заключение и точные источники. Сигналы требуют экспертной проверки и не являются доказанными нарушениями.

## Что получилось

**Изменение функции можно проследить до конкретного пункта исходного документа — вместе с ответственным подразделением и основанием вывода.**

На размеченной части синтетического DOCX-контроля финальный core `e1e87ba` получил: **функции 9 TP / 0 FP / 0 FN; подразделения 7 / 0 / 0; риски 2 / 0 / 0**. В обоих режимах отдельно проверены **209 цитат без ошибок**. GPT-5.5 самостоятельно завершил расследование: **9 ходов, 20 инструментов, `completed`**.

Это development-контроль с **19 `pending_human` labels**, не общая точность продукта. Для PDF остаются две неопределённости преемственности; они не скрыты. Полные исходные результаты, конфигурация и ограничения: [финальный пакет](docs/evidence/stage3-capture-e1e87ba-openai.zip), [машиночитаемый handoff](docs/evidence/stage3-freeze.json).

Frontend и offline-export поддерживают публичный Stage 3 контракт. Report и trace сохраняются и повторно читаются; старые `agent: null`/неоценённые поля не означают «рисков нет». Исторические `partial`-попытки сохранены отдельно. Внешний деплой не требуется: ниже приведён локальный запуск; для настоящего агентного режима нужен разрешённый backend-доступ к модели. Ключи не передаются в браузер и не входят в репозиторий.

## Основной путь: изолированный локальный запуск Windows

Требуются Git for Windows с Git shell/curl, PowerShell, Python 3.12, uv и Node.js 24. Проверенная конфигурация: Python 3.12.12, uv 0.9.21, portable Node 24.21.0. Docker/WSL на проверочной машине отсутствуют; Docker не является доказанным способом запуска этой поставки.

Установка разрешена только в отдельном checkout и одним integration owner. Используйте `uv.lock` и `apps/web/package-lock.json` без их перегенерации. Не запускайте `uv add`, `uv lock` или `npm install` в общей рабочей копии. Установка пакетов требует доступа к реестрам; она не разрешает платную модель или передачу документов внешнему сервису.

### 1. Закрепить ревизию и установить зависимости

В новом PowerShell без личных ключей:

```powershell
$Revision = "e1e87ba85a8d4f68908cf07922bb5a180f18b14d"
$Source = Read-Host "Путь к репозиторию с указанным коммитом или одобренный Git URL"
$Checkout = Join-Path $env:TEMP ("fla-check-" + [guid]::NewGuid().ToString("N"))
git clone --no-hardlinks --no-checkout $Source $Checkout
if ($LASTEXITCODE -ne 0) { throw "Clone failed" }
Set-Location $Checkout
git -c core.autocrlf=false checkout --detach $Revision
if ($LASTEXITCODE -ne 0) { throw "Pinned checkout failed" }
git rev-parse HEAD
git status --porcelain

$NodeHome = Read-Host "Каталог установленного Node 24 (с node.exe)"
$Node = Join-Path $NodeHome "node.exe"
$Npm = Join-Path $NodeHome "node_modules\npm\bin\npm-cli.js"
$env:PATH = "$NodeHome;$env:PATH"
& $Node --version
uv --version
uv sync --frozen --no-dev --no-install-project
if ($LASTEXITCODE -ne 0) { throw "Frozen Python install failed" }
Push-Location apps/web
& $Node $Npm ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw "Locked web install failed" }
Pop-Location
```

Не копируйте `.env` из личной/общей среды. В чистом checkout `b392d9b` все **4/4 организаторских источника** совпали с `seeds/kt/manifest.json`, включая исходные TXT; прежнее LF/CRLF-несоответствие больше не воспроизводится на этой ревизии. Все **8/8 основных файлов** control bundle отдельно совпали с его manifest. Не нормализуйте входные байты и не меняйте expected SHA.

### 2. Запустить API на loopback

Из корня этого checkout, в первом терминале (порт 19764 должен быть свободен):

```powershell
$env:LLM_API_KEY = ""
$env:DB_PATH = Join-Path (Get-Location) "data\review.db"
$env:DATA_DIR = Join-Path (Get-Location) "data"
$env:CORS_ORIGINS = "http://127.0.0.1:19874"
uv run --no-sync python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 19764
```

В другом терминале: `Invoke-RestMethod http://127.0.0.1:19764/healthz`. Для keyless-проверки обязательны `status: ok`, `db: ok`, `llm_configured: false`. Не продолжайте с неожиданно активной моделью. Наличие ключа само по себе не разрешает его использовать.

### 3. Собрать и запустить production frontend

Во втором терминале задайте те же `$Checkout`, `$NodeHome`, `$Node`, `$Npm` и PATH из шага 1:

```powershell
Set-Location (Join-Path $Checkout "apps\web")
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:19764"
$env:NEXT_TELEMETRY_DISABLED = "1"
& $Node $Npm run build
if ($LASTEXITCODE -ne 0) { throw "Web build failed" }
Copy-Item .next/static .next/standalone/.next/static -Recurse -Force
$env:HOSTNAME = "127.0.0.1"
$env:PORT = "19874"
& $Node .next/standalone/server.js
```

Откройте **http://127.0.0.1:19874**. Сохраните весь checkout с установленными зависимостями; перенос одного `server.js` не является проверенным deployment. `NEXT_PUBLIC_API_BASE` встраивается при сборке, а не при старте. Изменяя порты, согласованно меняйте API bind, CORS, web build URL и demo URL. Не освобождайте порты остановкой чужих процессов. Оба сервера завершайте Ctrl+C только в своих терминалах.

Next при production build обновляет generated `apps/web/next-env.d.ts`: пути `.next/dev/types` становятся `.next/types`. В проверочном checkout это единственное tracked-изменение после запуска; оно не является ручным изменением исходников или lockfiles. Не переносите этот generated diff в общую рабочую копию.

## Проверка реального сценария

Из корня pinned checkout, пока оба сервера работают:

```powershell
$GitShell = "C:\Program Files\Git\bin\sh.exe"
& $GitShell --version
$env:API_BASE_URL = "http://127.0.0.1:19764"
& $GitShell scripts/demo.sh
if ($LASTEXITCODE -ne 0) { throw "Audit failed" }
uv run --no-sync python scripts/export_report.py --report data/demo-report.json --out data/demo-report.html
if ($LASTEXITCODE -ne 0) { throw "Export failed" }
```

Скрипт загружает реальные `v8.docx`/`v9.docx`, отправляет `use_llm=false`, проверяет SSE и сохраняет единственный final Report. По умолчанию `API_BASE_URL` равен `http://localhost:8000`; это переменная только demo, не настройка web bundle. В PowerShell bare `sh` может отсутствовать; используйте полный путь Git shell, а не неподтверждённый WSL Bash.

Сравните **весь** сохранённый Report с публичным API:

```powershell
@'
import json, os
from pathlib import Path
from urllib.request import urlopen
saved = json.loads(Path("data/demo-report.json").read_text(encoding="utf-8"))
base = os.environ["API_BASE_URL"].rstrip("/")
with urlopen(base + "/audits/" + saved["run_id"], timeout=30) as response:
    assert json.load(response) == saved, "Persisted Report differs"
print("Persisted Report matches:", saved["run_id"])
'@ | uv run --no-sync python -
```

В браузере:

- Загрузите обе редакции или откройте сохранённый ID (`?run=...`). DOCX/PDF/XLSX/TXT принимаются; DOC/XLS требуют настоящей конвертации.
- Проверьте режим, состояние/область работы агента и фактические действия. Replay сохранённого trace явно отличается от нового запуска; внутренние SDK spans и скрытые рассуждения не показываются.
- Пройдите таблицы подразделений, функций, рисков; фильтр и пагинацию; заключение → результат → точную цитату → контекст/координаты. Исторические/null-поля остаются неоценёнными. Обычный ordinal не выдаётся за страницу PDF или блок DOCX.
- Скачайте полный Report JSON, откройте локально без отправки серверу. Откройте `data/demo-report.html` через `file://`: автономный HTML не требует SQLite, API, модели или сети.

Подробный экспертный проход: [demo](docs/demo.md). Публичный синтетический control bundle: [его инструкции](seeds/kt/eval/control/README.md). Он не является organiser gold; представления одного текста не нужно загружать одновременно как разные документы. Доступность формата не доказывает качество его семантического разбора.

## Агентный доступ для экспертов

Нужен согласованный неперсональный demo/test provider/model, разрешённые входные данные и лимит расходов либо реально проверенный self-hosted/local model. Подписка на coding assistant не предоставляет inference этому приложению. BYO-key, keyless fallback и записанный trace не закрывают этот gate.

До согласования не вызывайте внешнюю модель и не публикуйте приложение/документы. После согласования сначала проверьте синтетический комплект, реальные result-dependent tool actions, `Report.mode`, `agent.status`, stop reason, investigated subset, partial/failure и сохранение. Checkbox `use_llm` не доказывает работу агента. Собственный runtime Askat проверен keyless: `not_requested` или `unavailable`, ноль tool calls. Отдельно получены и сохранены backend OpenAI captures на `b392d9b`: completed `9c7199f33a9f4ca3a9a47abfd65b8c6f` и budget-limited partial `1c3f51541f754b20925f1d50ec47ec07`; [независимый review](docs/evidence/kt-quality.md) подтверждает действия в границах сохранённого DOCX-прогона, но не полную приёмку Stage 3. Нового вызова провайдера Askat и готового inference-маршрута для экспертов эта поставка не утверждает.

## Конфигурация и ограничения

Параметры backend перечислены в `.env.example`: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_S`, `LLM_MAX_TOKENS`, `DB_PATH`, `DATA_DIR`, `SEEDS_DIR`, `EMBED_MODEL`, `EMBED_DIM`, `API_HOST`, `API_PORT`, `CORS_ORIGINS`. Web читает `NEXT_PUBLIC_API_BASE` при сборке. Не сохраняйте секреты в Git; переменные окружения могут переопределять dotenv.

- Native dependencies закреплены locks. Изображения Docker и embedding weights не закреплены content digest; Docker/Compose здесь не запускались. Compose публикует 8000/3000 на всех интерфейсах: не используйте его на публичном хосте без согласованной изоляции.
- Проверены цифровые документы; OCR extra не устанавливался. Работа со сканами и произвольными оргсхемами не подтверждена.
- Проверенные control DOCX/PDF/XLSX на `b392d9b` содержат `Clause.location`: блок DOCX, физическую страницу PDF или лист/ячейки XLSX. Координаты не означают правильную семантику: PDF остаётся фрагментированным; оба проверенных XLSX-варианта не извлекают функции и не дают оценки межподразделенческих рисков. Нулевые результаты здесь не означают отсутствие изменений или рисков. Неизвестные координаты старых/других отчётов не выдумываются.
- `missing` означает отсутствие подтверждённого преемника в предоставленном комплекте, а не доказанную утрату. `duplicate`, межподразделенческие риски и `unresolved` требуют проверки.
- Исторические retrieval-метрики инфраструктурного kit не являются точностью аудита. Реальные, синтетические и held-out evidence разделены.

## Документы, происхождение и лицензия

- [Официальная задача](seeds/kt/TASK.md), [manifest организаторских материалов](seeds/kt/manifest.json)
- [Контракт](CONTRACT.md), [архитектура](docs/architecture.md), [бизнес-кейс](docs/business-case.md)
- [Launch evidence и backend handoff](docs/evidence/kt-launch.md), [quality evidence](docs/evidence/kt-quality.md), [PROGRESS](docs/PROGRESS.md)

Проект использует заранее подготовленный инфраструктурный kit: FastAPI, ingestion/retrieval, SQLite, SSE и Next.js. Аудит расширяет эти границы; kit отдельно описан в контракте и истории. Команда использовала AI coding assistance; утверждения о работе ограничены зафиксированными проверками. Личных API-ключей в поставке нет.

Код: [MIT](LICENSE). Обезличенные редакции 8/9 положения внутреннего аудита предоставлены организатором; отдельное ограничение hackathon-use записано в manifest.
