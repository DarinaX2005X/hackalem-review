# QALA LAB — Аким на 5 часов

Учебный AI-симулятор управления Астаной для HackAlem. Команда выбирает **ровно пять мероприятий** из общего каталога и распределяет **100 условных единиц**. Сервер рассчитывает результат на горизонте восьми кварталов, а OpenAI и NVIDIA объясняют готовые результаты.

## Локальный запуск

Нужен Python 3.10 или новее. Сторонние Python-пакеты не требуются.

```bash
cd hack-c03bcfc6-kaimak
python3 server.py
```

Открыть **http://127.0.0.1:8000**. После изменений Python-файлов перезапустите сервер: уже работающий процесс хранит прежний каталог в памяти. Для другого порта:

```bash
PORT=8001 python3 server.py
```

По умолчанию сервер доступен только на этом компьютере. `Ctrl+C` останавливает его. Шрифты загружаются из Google Fonts; без интернета используются системные шрифты. Расчёт, карта, сравнение и экспорт работают без внешних AI API.

Если каталог не загрузился, над ним остаётся сообщение с причиной и кнопка повторной загрузки. Интерфейс проверяет версию датасета и сообщает, если на порту работает старый сервер.

Инструкция подключения AI: [OpenAI и NVIDIA](#openai-и-nvidia).

## Источники и приоритет правил

- `task/HackAlem AI_ «Аким на 5 часов» - AI-симулятор управления городом.pdf` — техническое задание и критерии.
- `task/Датасет районов.docx` — исходные показатели, доли населения, 14 мероприятий, стоимости, задержки, эффекты, синергии, несовместимости, формула и подробные правила.
- `data.py` — явная транскрипция численных таблиц DOCX. Исходные документы сохранены в `task/`.

В общей формулировке ТЗ упомянуты пять направлений. Подробный датасет уточняет правила: **пять мер суммарно, максимум две из одного направления**, а не обязательная одна мера в каждом направлении. Пример из датасета содержит две социальные меры и не содержит транспортных. Приложение следует этим подробным правилам.

Районы: Есиль, Алматы, Сарыарка, Байконур, Нура. Используются доли населения, а не придуманные абсолютные численности. Все показатели учебные и направлены одинаково: больше — лучше. Стоимость выражена в условных единицах, не в тенге.

## Возможности

- **Выбор мероприятий:** 14 карточек с ценой, территорией действия, лагом и уже реализуемыми эффектами. Фильтрация по пяти направлениям.
- **План из пяти слотов:** добавление и удаление мер, остаток бюджета, цветовое распределение затрат и активные синергии.
- **Три стартовые стратегии:** точный пример из датасета, недорогой набор из датасета с выбранными районами, авторский вариант с транспортной синергией. Все состоят из исходных мер.
- **3D-город:** локальная Three.js r180, объёмные районы, здания, река и условный Байтерек. Мышь или касание вращает модель; кнопки и щипок меняют масштаб. Стрелки, `+`/`−` и `Home` доступны с клавиатуры при фокусе на сцене. Подписи районов — обычные доступные кнопки. Выбор района также меняет цель для новых мер. Цветные объекты показывают выбранные мероприятия; переключатель «до / после» синхронизирован с расчётом.
- **Атлас влияния:** интерактивная схема пяти районов, переключение «до / после», десять показателей каждого района, критический порог 40 и его влияние на Score. Схема не передаёт реальные границы районов.
- **Резервная схема:** переключение 3D / 2D; при отсутствии WebGL2, ошибке загрузки модуля или потере графического контекста используется 2D. Ошибка 3D не прерывает расчёт. Все файлы Three.js находятся в `static/vendor/`, CDN при запуске не нужен. Кадры рисуются при изменении вида или данных, постоянного цикла анимации нет.
- **Прозрачный Score:** отдельно показаны городской индекс, слабейший район и штраф. При неполном плане отображается прогноз черновика; итоговый Score не присваивается.
- **Следующий ход:** сервер перебирает все допустимые замены одной меры, включая перенос в другой район, и предлагает улучшение. Это локальный поиск, не утверждение о глобальном оптимуме.
- **Брифинг:** проверяемые сильные стороны, риски и последствия; по запросу — ответы OpenAI и NVIDIA с отдельным статусом каждого провайдера.
- **Паспорт сценария:** скачиваемый самостоятельный HTML с пятью решениями, эффектами, синергиями, результатами районов, десятью показателями и формулой. Можно открыть без сервера и распечатать в PDF.
- **Сравнение команд:** до 30 сценариев в текущем браузере, сортировка по Score, повторное открытие. При восстановлении сохранённых сценариев баллы пересчитываются сервером.
- **Черновик:** автоматически сохраняется в `localStorage`. Старые сценарии с вымышленными районами и бюджетом 1000 не смешиваются с новым датасетом.

## Правила валидатора

1. Ровно 5 решений для финального результата. Черновик может содержать 0–4.
2. Одно мероприятие нельзя выбрать повторно, даже для другого района.
3. Максимум 2 меры одного направления, то есть минимум 3 направления в полном наборе.
4. Для районной меры обязателен район. Для городской поле района отсутствует.
5. Суммарные затраты не превышают 100. Остаток сохраняется и не даёт бонуса.
6. M1 и M3 несовместимы в любых районах.
7. M4 и M7 запрещены в одном районе.
8. M5 и M13 запрещены в одном районе.

Любое нарушение отклоняется сервером с причиной. Ошибочная попытка не изменяет последний допустимый план. Для недопустимого набора Score не рассчитывается. Порядок добавления мер не влияет на результат.

## Формула датасета

Для каждого района и показателя:

```text
I′ = clip(I + Σ [эффект × (8 − лаг) / 8] + синергии, 0, 100)
D = Σ [вес показателя × I′]
D_avg = Σ [доля населения × D]
Score = 0.7 × D_avg + 0.3 × min(D) − N_crit
```

`N_crit` — число пар «район × показатель» со значением **строго ниже 40**. Ровно 40 штрафа не даёт. Сначала суммируются все эффекты и синергии, затем показатели ограничиваются диапазоном 0–100. Внутренние вычисления не округляются. Итог отображается до двух знаков.

| Показатель | T1 | T2 | E1 | E2 | S1 | S2 | B1 | B2 | C1 | C2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Вес | .10 | .10 | .09 | .11 | .11 | .11 | .09 | .09 | .10 | .10 |

Фиксированные бонусы не масштабируются лагом:

| Пара | Бонус | Территория |
|---|---|---|
| M1 + M2 | T1 +2 | Район M1 |
| M10 + M12 | B1 +2 | Район M10 |
| M5 + M6 | E2 +2 | Район M5 |

Исходный `D_avg = 56.8624`, слабейший район — Нура (`49.18`), критических показателей два (`S1=38`, `S2=35`). Базовый уровень `52.55768`, на экране — **52.56**.

`contributions` содержит эффекты каждой меры с учётом лага до итогового ограничения показателей. Синергии передаются отдельно. Вклады мер в Score не складываются линейно: минимум по районам, штрафы и ограничение диапазона зависят от комбинации.

## OpenAI и NVIDIA

### Подключение OpenAI через настройки сайта

1. Создайте ключ на странице [API keys в OpenAI Platform](https://platform.openai.com/api-keys). Инструкция OpenAI: [создание и подключение API key](https://developers.openai.com/api/docs/quickstart).
2. Запустите `python3 server.py` и откройте **http://127.0.0.1:8000**.
3. Вверху страницы нажмите **«Настройки»** рядом с переключателем языка.
4. Вставьте ключ `sk-…` в поле **OpenAI API key** и нажмите **«Сохранить»**. Поле скрывает символы. Сохранение проверяет формат, а доступ к API проверяется при первом разборе.
5. Выберите пять допустимых мероприятий (или загрузите пример) и нажмите **«AI-разбор стратегии»**. Ответ появится в разделе результатов с отдельным статусом OpenAI.

Ключ хранится только в памяти открытой страницы до её перезагрузки. Он не записывается в `localStorage`, `.env`, сохранённые сценарии или экспорт. При AI-разборе ключ передаётся серверу этого сайта, который выполняет запрос к OpenAI. Вводите его только в доверенной установке; при доступе через интернет используйте HTTPS.

Чтобы заменить ключ, снова откройте настройки и сохраните новый. **«Удалить ключ»** удаляет ключ из памяти страницы; после этого используется серверный ключ из `.env`, если он настроен. Закрытие окна без сохранения не меняет текущий ключ. Настройки доступны на русском, английском и казахском языках.

### Постоянное подключение через `.env`

Если ключ должен сохраняться после перезагрузки страницы, создайте `.env` в корне проекта по образцу `.env.example` (не перезаписывайте существующий файл) и заполните:

```dotenv
OPENAI_API_KEY=ваш_ключ_OpenAI
OPENAI_MODEL=gpt-4.1-mini
NVIDIA_API_KEY=
NVIDIA_MODEL=mistralai/mistral-nemotron
```

Перезапустите сервер после изменения `.env`. Переменные окружения имеют приоритет над `.env`; ключ из окна настроек имеет приоритет для конкретного AI-запроса и не меняет настройки других пользователей. NVIDIA необязательна: её ключ задаётся только на сервере. Без ключей работает локальный расчёт.

### Если OpenAI не отвечает

- **401 / ошибка авторизации:** проверьте ключ, замените отозванный или неверный ключ в настройках.
- **403 / нет доступа:** проверьте права проекта и доступ к модели `OPENAI_MODEL`.
- **429 / лимит:** проверьте квоту, оплату и лимиты своего API-проекта; повторите позже.
- **Таймаут / ошибка сети:** проверьте доступ сервера к OpenAI и повторите разбор.

### Как работает анализ

- **NVIDIA NIM**, Chat Completions: один подтверждённый данными риск и один вопрос для проверки перед реальным внедрением.
- **OpenAI**, Responses API: объяснение стратегии на основе расчёта. Ответ NVIDIA передаётся как гипотеза, а не проверенный факт.
- Оба получают бюджет, исходный и итоговый Score, изменения районов и индикаторов, эффекты мер, синергии, критические значения и результат поиска замены.
- AI не считает и не изменяет Score. Ответы моделей имеют отдельную маркировку.
- API вызываются только по кнопке **«AI-разбор стратегии»**. Обычная работа с планом не расходует API-квоту.
- Таймауты: NVIDIA 20 секунд, OpenAI 35 секунд; запросы последовательные.
- При недоступности провайдера локальный расчёт и второй провайдер продолжают работать. UI различает отсутствие ключа, 401, 403, 410, 429, таймаут и сетевую ошибку.

Ключи не включаются в исходники, ответы API, паспорт или логи. Введённый пользователем ключ временно хранится в памяти JavaScript этой страницы. HTTP-маршруты обслуживают только явно перечисленные файлы; `.env` через сервер не отдаётся. Не публикуйте `.env`.

## API

`GET /api/bootstrap` — версия датасета, правила, каталог, районы, индикаторы, стартовые стратегии и исходный расчёт.

`POST /api/analyze` принимает `choices`, необязательный `lang` (`ru`, `en`, `kk`) и необязательный `openai_api_key`. Ключ используется только для данного запроса, не возвращается в ответе и не изменяет окружение сервера. Не передавайте ключ в URL.

`POST /api/simulate` — допустимый черновик или полный набор. Полный набор включает локальный анализ и рекомендацию. Внешние API не вызываются.

```json
{
  "choices": [
    {"action": "M7", "district": "nura"},
    {"action": "M8", "district": "nura"},
    {"action": "M10", "district": "nura"},
    {"action": "M12"},
    {"action": "M5", "district": "saryarka"}
  ]
}
```

`POST /api/analyze` — тот же формат, обязательно 5 мер; добавляет `providers.openai` и `providers.nvidia` со статусами и текстами.

Для неполного набора `score` равен `null`, `projected_score` содержит только прогноз черновика. Ошибка валидации: HTTP 400 и `{"error": "причина"}`. Длина запроса ограничена 16 КБ.

## Структура

```text
server.py          HTTP-маршруты и запуск
engine.py          валидация, формула, синергии, объяснение, поиск замены
data.py            транскрипция датасета и стартовые стратегии
ai.py              .env и интеграции провайдеров
static/index.html  интерфейс и схема районов
static/style.css   адаптивная тема
static/app.js      управление планом, карта, хранение, экспорт
static/city3d.js    сцена, управление камерой, выбор районов, отображение мер
static/vendor/     Three.js r180 и оригинальная MIT-лицензия
 task/             исходные задания и данные
```

Это локальный прототип: совместной базы команд и авторизации нет. Для обмена результатом скачайте паспорт. Сервер использует стандартный HTTP-сервер Python и предназначен для локальной демонстрации.

### 3D и исходные данные

Геометрия и количество зданий — иллюстрация, а не данные о застройке или населении. Районы расположены схематично. Ни высоты зданий, ни объекты мер не участвуют в формуле Score. Для «до» показываются исходные индикаторы, для «после» — результат API. Цвет площадки отмечает наличие показателя ниже 40; отдельный контур отмечает выбранный район.

Three.js закреплена на версии r180: [официальный репозиторий](https://github.com/mrdoob/three.js/tree/r180). Лицензия сохранена в `static/vendor/THREE-LICENSE.txt`. 3D требует поддержки WebGL2 браузером и видеодрайвером.

## Языки и темы

В шапке доступны две кнопки с иконками: глобус переключает **Русский → English → Қазақша**, луна/солнце переключает две темы:

- **Светлая** — светлая сиреневая тема с фиолетовыми акцентами; включена по умолчанию.
- **Тёмная** — повышенный контраст текста на тёмном фоне.

Язык и тема сохраняются отдельно от плана в `qala-preferences-v1`. Переключение не меняет решения, бюджет и Score. Основной текст увеличен до 16–18 px; размеры кнопок, карточек и вспомогательного текста также увеличены. На узком экране меры перестраиваются в одну колонку.

`static/locales.json` содержит переводы интерфейса, каталога, показателей, ошибок, локальных объяснений и экспорта на три языка. Казахская версия использует кириллицу. Имена сценариев, введённые пользователем, сохраняются как введены. Числа форматируются через `Intl` для выбранного языка. Отчёт скачивается как `qala-scenario-ru.html`, `qala-scenario-en.html` или `qala-scenario-kk.html`.

При запросе AI-разбора клиент отправляет `lang: "ru" | "en" | "kk"`. Сервер задаёт язык ответа обоим провайдерам. Само переключение языка **не вызывает API**. Ответы в памяти разделены по языкам; при изменении плана кэш ответов сбрасывается. Текстовые объяснения в UI используют готовые числа сервера, формула остаётся в `engine.py`.

Новые статические файлы: `preferences.js` (раннее применение настроек), `themes.css` (темы и читаемость), `locales.json` (переводы). После обновления нужно перезапустить `server.py`, чтобы новые маршруты стали доступны.


---

# QALA LAB — Mayor for 5 Hours

An educational AI simulator for managing Astana, built for HackAlem. Teams select **exactly five measures** from a shared catalogue and allocate **100 budget units**. The server calculates outcomes over eight quarters, while OpenAI and NVIDIA explain the calculated results.

## Running locally

Python 3.10 or newer is required. No third-party Python packages are needed.

```bash
cd hack-c03bcfc6-kaimak
python3 server.py
```

Open **http://127.0.0.1:8000**. Restart the server after changing Python files: a running process keeps the previous catalogue in memory. To use another port:

```bash
PORT=8001 python3 server.py
```

By default, the server is accessible only from your computer. Press `Ctrl+C` to stop it. Fonts load from Google Fonts; system fonts are used offline. Calculations, maps, comparisons, and exports work without external AI APIs.

If the catalogue fails to load, an error message and a retry button remain visible above it. The interface checks the dataset version and warns if an outdated server is running on the port.

## Sources and rule precedence

- `task/HackAlem AI_ «Аким на 5 часов» - AI-симулятор управления городом.pdf` — project brief and evaluation criteria.
- `task/Датасет районов.docx` — baseline indicators, population shares, 14 measures, costs, delays, effects, synergies, incompatibilities, the formula, and detailed rules.
- `data.py` — an explicit transcription of the numerical DOCX tables. Original documents are preserved in `task/`.

The general brief mentions five policy categories. The detailed dataset specifies **five measures in total, with at most two per category**, rather than requiring one measure from each category. Its example includes two social measures and no transport measures. The application follows these detailed rules.

Districts: Yesil, Almaty, Saryarka, Baikonur, and Nura. The simulator uses population shares rather than invented population totals. All indicators are educational and share the same direction: higher is better. Costs are expressed in budget units, not tenge.

## Features

- **Measure selection:** 14 cards showing cost, scope, delay, and effects realized within the simulation period. Filter by five policy categories.
- **Five-slot plan:** add and remove measures, track the remaining budget, view spending by colour, and see active synergies.
- **Three starting strategies:** the exact dataset example, an inexpensive dataset selection with assigned districts, and a custom transport-synergy strategy. All use the original measures.
- **3D city:** locally bundled Three.js r180, districts, buildings, a river, and a stylized Baiterek. Rotate with a mouse or touch; zoom with buttons or a pinch gesture. Arrow keys, `+`/`−`, and `Home` work when the scene has focus. District labels are accessible buttons. Selecting a district also sets the target for new measures. Coloured objects represent selected measures; the before/after switch stays synchronized with calculations.
- **Impact atlas:** an interactive diagram of five districts, before/after views, ten indicators per district, and the critical threshold of 40 with its effect on Score. The diagram does not represent actual district boundaries.
- **Fallback map:** switch between 3D and 2D. The app falls back to 2D if WebGL2 is unavailable, a module fails to load, or the graphics context is lost. A 3D error does not interrupt calculations. All Three.js files are in `static/vendor/`; no CDN is needed at runtime. Frames render when the view or data changes, without a continuous animation loop.
- **Transparent Score:** the city index, weakest district, and penalty are shown separately. Incomplete plans show a draft projection, without a final Score.
- **Next move:** the server checks all valid single-measure replacements, including moves to another district, and suggests an improvement. This is a local search, not a claim of global optimality.
- **Briefing:** verifiable strengths, risks, and consequences; on request, OpenAI and NVIDIA responses with separate provider statuses.
- **Scenario report:** a downloadable, standalone HTML file containing five decisions, effects, synergies, district results, ten indicators, and the formula. Open it without the server or print it to PDF.
- **Team comparison:** store up to 30 scenarios in the current browser, sort by Score, and reopen them. The server recalculates scores when saved scenarios are restored.
- **Draft saving:** automatic persistence in `localStorage`. Old scenarios with fictional districts and a budget of 1,000 are kept separate from the new dataset.

## Validation rules

1. Exactly 5 decisions are required for a final result. Drafts may contain 0–4.
2. A measure cannot be selected twice, even for different districts.
3. At most 2 measures may belong to one category, so a complete plan covers at least 3 categories.
4. District-level measures require a district. Citywide measures omit the district field.
5. Total spending must not exceed 100. Unspent funds remain available and provide no bonus.
6. M1 and M3 are incompatible regardless of district.
7. M4 and M7 cannot be assigned to the same district.
8. M5 and M13 cannot be assigned to the same district.

The server rejects violations with a reason. An invalid attempt leaves the last valid plan unchanged. Invalid plans receive no Score. The order in which measures are added does not affect the result.

## Dataset formula

For each district and indicator:

```text
I′ = clip(I + Σ [effect × (8 − delay) / 8] + synergies, 0, 100)
D = Σ [indicator weight × I′]
D_avg = Σ [population share × D]
Score = 0.7 × D_avg + 0.3 × min(D) − N_crit
```

`N_crit` counts district–indicator pairs with values **strictly below 40**. A value of exactly 40 incurs no penalty. All effects and synergies are summed before indicators are clipped to 0–100. Internal calculations are not rounded. Results are displayed to two decimal places.

| Indicator | T1 | T2 | E1 | E2 | S1 | S2 | B1 | B2 | C1 | C2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Weight | .10 | .10 | .09 | .11 | .11 | .11 | .09 | .09 | .10 | .10 |

Fixed synergy bonuses are not scaled by delay:

| Pair | Bonus | Scope |
|---|---|---|
| M1 + M2 | T1 +2 | M1's district |
| M10 + M12 | B1 +2 | M10's district |
| M5 + M6 | E2 +2 | M5's district |

Initially, `D_avg = 56.8624`, the weakest district is Nura (`49.18`), and two indicators are critical (`S1=38`, `S2=35`). The baseline is `52.55768`, displayed as **52.56**.

`contributions` contains each measure's effects after accounting for delay, before final indicator clipping. Synergies are returned separately. Contributions to Score are not linearly additive: the weakest district, penalties, and clipping depend on the combination of measures.

## OpenAI and NVIDIA

The server reads settings from `.env` in the project root. Environment variables take precedence. Use `.env.example` as a template without overwriting an existing `.env`.

```dotenv
OPENAI_API_KEY=
NVIDIA_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
NVIDIA_MODEL=mistralai/mistral-nemotron
```

- **NVIDIA NIM**, Chat Completions: one risk supported by the data and one question to investigate before real-world implementation.
- **OpenAI**, Responses API: an explanation of the strategy based on calculated results. NVIDIA's response is passed as a hypothesis, not a verified fact.
- Both receive the budget, baseline and final Score, district and indicator changes, measure effects, synergies, critical values, and the replacement-search result.
- AI neither calculates nor changes Score. Model responses are labelled separately.
- APIs are called only when the **AI strategy review** button is pressed. Normal plan editing does not consume API quota.
- Timeouts: 20 seconds for NVIDIA and 35 seconds for OpenAI; requests run sequentially.
- If a provider is unavailable, local calculations and the other provider continue working. The UI distinguishes missing keys, 401, 403, 410, 429, timeouts, and network errors.

Keys are not included in HTML, JavaScript, API responses, exported reports, or logs. HTTP routes serve only explicitly listed files; `.env` is never served. Do not publish `.env`.

## API reference

`GET /api/bootstrap` — dataset version, rules, catalogue, districts, indicators, starting strategies, and baseline calculations.

`POST /api/simulate` — accepts a valid draft or complete plan. Complete plans include local analysis and a recommendation. No external APIs are called.

```json
{
  "choices": [
    {"action": "M7", "district": "nura"},
    {"action": "M8", "district": "nura"},
    {"action": "M10", "district": "nura"},
    {"action": "M12"},
    {"action": "M5", "district": "saryarka"}
  ]
}
```

`POST /api/analyze` — uses the same format, requires 5 measures, and adds `providers.openai` and `providers.nvidia` with statuses and response text.

For incomplete plans, `score` is `null` and `projected_score` contains only the draft projection. Validation errors return HTTP 400 with `{"error": "reason"}`. Request bodies are limited to 16 KB.

## Project structure

```text
server.py          HTTP routes and startup
engine.py          validation, formula, synergies, explanations, replacement search
data.py            dataset transcription and starting strategies
ai.py              .env loading and provider integrations
static/index.html  interface and district diagram
static/style.css   responsive styling
static/app.js      plan management, map, storage, export
static/city3d.js    scene, camera controls, district selection, measure visualization
static/vendor/     Three.js r180 and its original MIT license
task/              original brief and datasets
```

This is a local prototype without a shared team database or authentication. Download a scenario report to share results. The server uses Python's standard HTTP server and is intended for local demonstrations.

### 3D and source data

Geometry and building counts are illustrations, not construction or population data. District placement is schematic. Neither building heights nor measure objects affect the Score formula. The before view uses baseline indicators; the after view uses API results. Platform colours indicate whether any indicator is below 40; a separate outline marks the selected district.

Three.js is pinned to r180: [official repository](https://github.com/mrdoob/three.js/tree/r180). Its license is stored in `static/vendor/THREE-LICENSE.txt`. 3D requires WebGL2 support in the browser and graphics driver.

## Languages and themes

The header has two icon buttons: the globe cycles through **Русский → English → Қазақша**, and the moon/sun switches between two themes:

- **Light** — a pale lilac theme with purple accents; enabled by default.
- **Dark** — higher-contrast text on a dark background.

Language and theme preferences are stored separately from the plan in `qala-preferences-v1`. Switching them does not change decisions, budget, or Score. Main text is 16–18 px; buttons, cards, and supporting text are also enlarged. Measures use a single-column layout on narrow screens.

`static/locales.json` contains translations of the interface, catalogue, indicators, errors, local explanations, and exports in all three languages. Kazakh uses Cyrillic. User-entered scenario names are preserved as entered. Numbers are formatted with `Intl` for the selected language. Reports download as `qala-scenario-ru.html`, `qala-scenario-en.html`, or `qala-scenario-kk.html`.

When requesting an AI review, the client sends `lang: "ru" | "en" | "kk"`. The server sets the response language for both providers. Switching languages alone **does not call the APIs**. Responses are cached in memory separately by language; changing the plan clears the response cache. UI explanations use numbers already calculated by the server; the formula remains in `engine.py`.

Additional static files: `preferences.js` applies preferences early, `themes.css` defines themes and readability styles, and `locales.json` provides translations. Restart `server.py` after updating so that new routes become available.
