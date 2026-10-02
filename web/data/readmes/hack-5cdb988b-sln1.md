# HackAlem AI — Track 05: Logistics

## Задание 01 — «Автоматический расчёт заказов поставщикам для пополнения склада»

**Владелец задачи:** ТОО «Электрокомплект»  
**Основной пользователь:** менеджер отдела закупа

Решение автоматизирует подготовку рекомендаций по пополнению склада: пользователь загружает исходные файлы, система рассчитывает рекомендуемые количества по поставщикам, показывает срочность и объяснение, после чего менеджер проверяет и подтверждает результат.

> Заказы поставщикам автоматически не отправляются. Финальное решение остаётся за ответственным сотрудником.

---

## 1. Что должно решать решение

По официальному ТЗ расчёт должен учитывать:

- историю продаж;
- текущие остатки;
- товары в пути;
- категории товаров;
- сезонность;
- устойчивый рост спроса;
- прогноз прироста;
- упущенный спрос в периоды stockout;
- разовые крупные заказы и выбросы;
- поставщиков и сроки поставки.

Целевой сценарий:

```text
загрузка файлов
→ обработка данных
→ расчёт рекомендаций
→ просмотр по поставщикам
→ проверка объяснений
→ корректировка / подтверждение
→ экспорт
```

---

## 2. Current status

**MVP полностью рабочий end-to-end**, проверено на настоящих файлах партнёра (не на моках):

- все 6 файлов IEK + все 6 файлов SystemElectric загружены одним запросом → **0 ошибок**, 3181 SKU по IEK и 724 SKU по SystemElectric;
- extractor реально парсит CSV (cp1251, `;`), а не отдаёт preview;
- ответ backend проходит собственную валидацию dashboard (`validateData`) без ошибок;
- повторная частичная загрузка (например, только обновлённый "Товар в пути") не стирает ранее загруженных поставщиков — backend хранит фрагменты в SQLite и на каждый запрос пересчитывает и возвращает всех известных поставщиков.

| Компонент | Статус |
|---|---|
| Dashboard | **Implemented** |
| `POST /api/upload` | **Implemented** |
| FastAPI backend | **Implemented** |
| SQLite cache (переживает рестарт backend'а) | **Implemented** |
| Расчёт по SKU | **Implemented** |
| Сезонность | **Implemented** |
| Stockout compensation | **Implemented** |
| Учёт текущего остатка | **Implemented** |
| Учёт товара в пути с датами поставок | **Implemented** |
| Дефицит по датам (запас закончится / поставка придёт) | **Implemented** |
| Базовое исключение крупных выбросов | **Implemented** |
| Влияние категории на расчёт | **Implemented** |
| Supplier grouping | **Implemented** |
| Explanation | **Implemented** |
| Urgency | **Implemented** |
| CSV export | **Implemented** |
| Human approval в UI | **Implemented** |
| CSV extractor (IEK + SystemElectric) | **Implemented** |
| End-to-end реальные файлы → рекомендации | **Implemented, verified** |
| Customer-level anomaly по `customer_id` | **Not implemented** (в данных партнёра нет обезличенного ID клиента) |
| Устойчивый trend / growth (отдельно от сезонности) | **Not implemented** |
| Отдельный forecast growth input | **Not implemented** |
| Supplier-specific lead time | **Not implemented** (фиксировано 30 дней) |
| Интеграция с 1С | **Not implemented** |
| Автоматическая отправка поставщику | **Not implemented by design** |

---

## 3. Архитектура

Рабочий поток (проверен end-to-end на реальных файлах):

```text
Dashboard
   │
   │ POST /api/upload (несколько файлов, multipart)
   ▼
FastAPI backend
   │
   ├─ каждый файл отдельным запросом → extractor /extract
   ├─ canonical fragment {supplier, file_type, items} → SQLite (upsert по поставщик+тип файла)
   ├─ сборка полного набора по КАЖДОМУ известному поставщику из накопленных фрагментов
   └─ process_supplier(...) по каждому
            │
            ▼
       JSON recommendations (все поставщики, не только из этого запроса)
            │
            ▼
Dashboard
→ таблица
→ фильтры
→ approve
→ CSV export
```

Для расчёта backend ожидает фрагменты типов:

```text
sales
stock
transit
```

Дополнительно поддерживается:

```text
moq
```

Файлы `Сезонность` и `Ежемесячные продажи в количественном выражении` extractor распознаёт и принимает (не выдаёт ошибку), но их содержимое не используется в расчёте — сезонность и агрегаты считаются внутри `process_supplier` из сырой истории продаж.

Каждый запрос к `/api/upload` пересчитывает и возвращает **всех** поставщиков, известных backend'у, а не только тех, чьи файлы пришли в этом запросе — иначе частичная догрузка одного поставщика убирала бы остальных из ответа и, соответственно, с экрана.

---

## 4. API

### `POST /api/upload`

Принимает несколько файлов одним multipart-запросом:

```text
multipart/form-data
files: File[]
```

Backend:

1. отправляет каждый файл в extractor **отдельным** запросом (по одному файлу за раз);
2. сохраняет canonical fragments в SQLite (upsert по `supplier + file_type`, старая версия этого типа файла для поставщика полностью заменяется);
3. собирает полные данные по **всем** известным поставщикам из накопленных фрагментов;
4. запускает `process_supplier(...)` по каждому;
5. возвращает готовый JSON, включая поставщиков, не затронутых этим конкретным запросом.

Ожидаемый ответ:

```json
{
  "generated_at": "2026-09-23",
  "suppliers": [
    {
      "supplier": "IEK",
      "items": [
        {
          "sku": "SKU-001",
          "name": "Товар",
          "category": "Категория",
          "current_stock": 20,
          "in_transit_qty": 10,
          "recommended_qty": 55,
          "urgency": "critical",
          "reason": "Краткое объяснение расчёта"
        }
      ]
    }
  ],
  "errors": []
}
```

`urgency`:

```text
critical
soon
planned
```

### `POST /api/recalculate`

Принимает уже нормализованные данные и запускает расчёт без загрузки файлов.

### `GET /api/health`

```json
{
  "status": "ok"
}
```

---

## 5. Методология расчёта

Расчёт выполняется по каждому SKU внутри `process_supplier(...)`.

### 5.1. Исключение крупных разовых транзакций

Используется robust-эвристика:

```text
large transaction:
abs(qty) > median(abs(qty)) × 4
```

Крупные операции исключаются из регулярного спроса только если они редкие:

```text
share of large transactions <= 15%
```

Если крупные продажи повторяются часто, алгоритм не исключает их автоматически.

> Ограничение: отдельный анализ аномалии по обезличенному `customer_id` пока не реализован.

### 5.2. Агрегация спроса

После очистки продажи агрегируются по месяцам:

```text
YYYY-MM → sum(qty)
```

### 5.3. Stockout / упущенный спрос

Stockout определяется только по данным остатков:

```text
monthly_stock <= 0
```

Нулевые продажи сами по себе stockout не означают.

Для stockout-месяца спрос восстанавливается:

1. по среднему спросу того же календарного месяца в другие годы;
2. если такой истории нет — по среднему non-stockout спросу.

### 5.4. Сезонность

Для каждого календарного месяца рассчитывается:

```text
seasonality_index =
average demand for calendar month
/
average demand for all months
```

### 5.5. Forecast

Текущий forecast использует последние `6` месяцев:

```text
recent mean
→ deseasonalization
→ seasonal coefficient target month
```

> Отдельный устойчивый trend / growth factor пока не реализован.

### 5.6. Категория и safety stock

Для категории рассчитывается волатильность:

```text
CV = std(monthly demand) / mean(monthly demand)
```

Страховой запас:

```text
safety_stock_days = 7 × (1 + average category CV)
```

с ограничением:

```text
5 ≤ safety_stock_days ≤ 21
```

### 5.7. Товар в пути: даты поставок, а не одно число

Вход — не одно число "сколько в пути", а список поставок с датой прибытия:

```text
incoming_shipments: [{ qty, expected_date }, ...]
```

Для IEK дата извлекается прямо из заголовка колонки файла "Товар в пути" (например, "поступление до 10.10.2026"). Для SystemElectric, где файл не содержит дат прихода, вся партия считается пришедшей "завтра" — это единственное текущее упрощение для этого поставщика.

В расчёт объёма заказа засчитывается только то, что придёт **в пределах горизонта поставки** (`lead_time_days`):

```text
qty_arriving_in_lead_time =
sum(qty for shipments where today <= expected_date <= today + lead_time_days)
```

Поставки, которые придут позже этого окна, в объём заказа не засчитываются — они не помогут закрыть ближайшую потребность.

### 5.8. Рекомендуемое количество

Текущий default lead time:

```text
30 дней
```

Формула:

```text
daily_forecast = monthly_forecast / 30

demand_for_lead_time =
daily_forecast × lead_time_days

safety_stock =
daily_forecast × safety_stock_days

raw_need =
demand_for_lead_time
+ safety_stock
- current_stock
- qty_arriving_in_lead_time

recommended_qty =
max(0, raw_need)
```

Если задан `MOQ`, заказ округляется вверх до кратности MOQ.

### 5.9. Дефицит по датам

Отдельно от объёма заказа считается **дата исчерпания запаса** — симуляция дня за днём: текущий остаток тратится по `daily_forecast`, а каждая известная поставка пополняет его на свою дату. Если очередная поставка приходит позже, чем закончится запас — это дефицит, `reason` явно называет обе даты:

```text
"запаса хватит до 2026-10-05, ближайшая поставка ожидается 2026-10-15 - вероятен дефицит на 10 дн."
```

Если дефицита нет — обоснование говорит, до какой даты хватит запаса с учётом поставок. Именно эта дата (не плоское число дней) используется для определения срочности.

### 5.10. Срочность

По дням до расчётной даты исчерпания запаса (см. 5.9):

```text
< 7 дней   → critical
< 21 дня   → soon
>= 21 дня  → planned
```

---

## 6. Explainability

Для каждой рекомендации формируется `reason`, который может включать:

- прогноз спроса;
- сезонный коэффициент;
- страховой запас;
- категорию;
- stockout-коррекцию;
- исключённые крупные заказы;
- дни покрытия текущим остатком;
- предупреждение об отсутствии актуального остатка.

---

## 7. Dashboard

Dashboard реализован на:

```text
HTML
CSS
JavaScript ES Modules
```

Поддерживаются:

- выбор нескольких файлов;
- drag & drop;
- удаление файлов перед отправкой;
- один синхронный `POST /api/upload`;
- loading state;
- HTTP/network/JSON error states;
- partial errors;
- KPI;
- поиск;
- фильтр поставщика;
- фильтр срочности;
- группировка по поставщикам;
- раскрываемое explanation;
- approve по одной позиции;
- approve видимых позиций поставщика;
- фильтр подтверждённых;
- CSV export.

`dashboard/mock_recommendations.json` используется **только как fixture для frontend-тестов**. Рабочий dashboard его не загружает.

Корневой `mock_recommendations.json` удалён как неиспользуемый.

---

## 8. Структура проекта

```text
.
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   ├── dashboard.mjs
│   ├── recommendations.mjs
│   ├── mock_recommendations.json
│   ├── package.json
│   └── tests/
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── storage.py
│   ├── calc_engine/
│   │   └── pipeline.py
│   └── extractor/
│       └── Extractor/
├── tests/
│   ├── test_api.py
│   ├── test_pipeline.py
│   └── fixtures/
├── Docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 9. Установка

### Python

Требуется Python 3.11+.

```bash
python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

### Dashboard tests

Для frontend-тестов требуется Node.js.

```bash
npm ci --prefix dashboard
```

### Extractor

Extractor — ASP.NET Core приложение. Для локального запуска требуется .NET SDK либо Docker.

---

## 10. Запуск

### Основной backend + dashboard

FastAPI сам раздаёт содержимое `dashboard/`, поэтому для локального запуска достаточно:

Linux / macOS:

```bash
PYTHONPATH=src uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Dashboard:

```text
http://127.0.0.1:8001/
```

Health check:

```text
http://127.0.0.1:8001/api/health
```

Так dashboard и `/api/upload` работают с одного origin.

### Только просмотр dashboard без API

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory dashboard
```

Открыть:

```text
http://127.0.0.1:8000/
```

В этом режиме UI доступен, но `/api/upload` отсутствует.

### Docker Compose

```bash
docker compose up --build
```

Сервисы:

```text
extractor : 8080
backend   : 8001
```

Dashboard входит в образ backend и раздаётся через FastAPI.

---

## 11. Environment variables

`.env.example`:

```env
OPENAI_API_KEY=
```

Backend также использует:

```text
EXTRACTOR_URL
UPLOADS_DB_PATH
```

В `docker-compose.yml` они задаются для backend автоматически.

`OPENAI_API_KEY` не требуется для текущей работы `/extract` — парсинг детерминированный (без LLM), переменная оставлена в `.env.example` как задел на будущее и может быть пустой/любой.

Секреты не должны попадать в Git.

---

## 12. Тестирование

### Backend / calculation engine

```bash
PYTHONPATH=src pytest -q
```

Проверено на текущем архиве:

```text
15 passed
```

### Dashboard

```bash
npm test --prefix dashboard
npm run check --prefix dashboard
```

Проверено на текущем архиве:

```text
19 passed
```

Frontend-тесты покрывают:

- выбор и удаление файлов;
- drag & drop;
- multipart POST;
- loading state;
- защиту от повторной отправки;
- обновление результатов;
- HTTP/network/JSON errors;
- partial errors;
- фильтры;
- approve;
- explanation;
- CSV export.

Backend-тесты покрывают:

- сезонность;
- stockout compensation;
- устойчивость к крупной разовой продаже;
- влияние `in_transit`/дат поставок;
- влияние категории;
- explanation;
- urgency;
- API contracts;
- SQLite cache и частичные обновления;
- возврат всех известных поставщиков на каждый запрос;
- деградацию при недоступном/некорректно отвечающем extractor.

Дополнительно вручную (не автоматизировано) проверено: все 12 реальных файлов IEK + SystemElectric за один запрос — 0 ошибок, 3181 + 724 SKU, ответ проходит `validateData` дашборда.

---

## 13. Must Have — текущее покрытие

| Требование | Статус |
|---|---|
| Базовый расчёт по SKU (все источники, изменение любого влияет на результат) | **Implemented** |
| История продаж | **Implemented** |
| Текущие остатки | **Implemented** |
| Товары в пути (с датами поставок) | **Implemented** |
| Категория товара (влияет на safety stock) | **Implemented** |
| Forecast growth input | **Not implemented** |
| Сезонность | **Implemented** |
| Устойчивый рост спроса | **Not implemented separately** (учтён неявно через тренд последних 6 мес.) |
| Дефицит по датам с учётом поставок | **Implemented** |
| Stockout / lost demand | **Implemented** |
| Крупные разовые заказы | **Implemented at transaction level** |
| Крупная продажа одному клиенту | **Not implemented separately** (в данных партнёра нет обезличенного ID клиента) |
| Supplier grouping | **Implemented** |
| Recommended quantity | **Implemented** |
| Urgency | **Implemented** |
| Explanation | **Implemented** |
| Dashboard / table | **Implemented** |
| Export | **Implemented: CSV** |
| Human approval | **Implemented in dashboard** |
| Автоматическая отправка поставщику | **Intentionally not implemented** |

---

## 14. Ограничения текущего MVP

1. Определение поставщика/типа файла — по имени файла (плюс резервная эвристика по содержимому для файла продаж IEK, где в имени файла нет бренда). Если партнёр когда-нибудь пришлёт файл с совсем другим именем — потребуется расширить эвристику.
2. Customer-level anomaly detection по обезличенному клиенту отсутствует — в предоставленных данных партнёра нет поля с ID клиента.
3. Отдельный устойчивый trend / growth отсутствует — учитывается неявно через тренд последних 6 месяцев.
4. Внешний forecast growth не передаётся в расчёт.
5. Lead time сейчас фиксирован значением `30` дней (не по поставщику).
6. Для SystemElectric нет дат поставок в исходном файле "Товар в пути" — весь объём считается приходящим "завтра"; для IEK даты извлекаются из файла по-настоящему.
7. Нет прямой интеграции с 1С.
8. Approve — UI-состояние, а не размещение заказа у поставщика.
9. Extractor не использует LLM — парсинг детерминированный (regex/CSV), `OPENAI_API_KEY` не задействован.

---

## 15. Privacy & Security

- клиентские данные должны оставаться обезличенными;
- нельзя использовать неанонимизированные данные клиентов;
- API keys и пароли не должны попадать в Git;
- исходные данные партнёра не должны публиковаться без разрешения;
- `.env` не должен коммититься;
- итоговые рекомендации проверяет ответственный сотрудник;
- заказ не отправляется поставщику автоматически.

---

## 16. Ближайшие TODO

P0 (end-to-end на реальных файлах) — **выполнено**:

- [x] привести `/extract` к canonical fragment contract;
- [x] прогнать реальные файлы поставщиков через `/api/upload`;
- [x] выполнить полный smoke test:
  `upload → extract → cache → calculate → JSON → dashboard`.

Дальше, по приоритету:

- [ ] даты поставок для SystemElectric (сейчас только IEK даёт реальные даты из файла);
- [ ] customer-level anomaly detection (нужен ID клиента от партнёра);
- [ ] устойчивый trend / growth отдельно от сезонности;
- [ ] forecast growth input;
- [ ] supplier-specific lead time.
