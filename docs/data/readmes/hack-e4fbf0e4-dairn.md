# DAIRN — ассистент для сайта EKT

Проект команды DAIRN для хакатона: веб-интерфейс с чатом, backend ассистента
и отдельный сервис интеграции с каталогом EKT. Условия задачи — в
[hackathon-task.json](hackathon-task.json).

## Состав проекта

| Компонент | Назначение |
| --- | --- |
| [frontend-service](frontend-service/) | React + TypeScript: интерфейс сайта, чат и отображение товаров |
| [assistant-service](assistant-service/) | FastAPI: сессии, сообщения, вложения и сценарии корзины; для обработки нужен отдельный worker |
| [ekt-catalog-service](ekt-catalog-service/) | Kotlin/JVM + Ktor: клиент EKT, нормализация, Catalog API, CLI и опциональный AI-поиск кандидатов |

Корневой [docker-compose.yml](docker-compose.yml) объединяет три сервиса и worker
в общей Docker-сети. Сервисные Compose-файлы предназначены для независимого запуска.

## Запуск всего приложения

Корневой [docker-compose.yml](docker-compose.yml) запускает frontend, Catalog API,
Assistant API и обязательный worker. Нужны Docker Engine, Compose plugin и доступ
к EKT API. Node.js, Python и Java на Docker-хосте не требуются: они входят в образы.
Все команды ниже выполняются из корня репозитория.

```sh
# Создать конфигурацию только при первом запуске; не перезаписывать существующую.
umask 077
if [ ! -f .env ]; then cp .env.example .env; fi
chmod 600 .env
nano .env

# Заполнить EKT_API_USERNAME, EKT_API_PASSWORD и PUBLIC_FRONTEND_URL.
# Для ответов модели также задать ASSISTANT_MODEL_API_KEY и ASSISTANT_MODEL_NAME.
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
```

Корневой Compose читает **корневой `.env`**. Файлы `.env` внутри сервисов для этого
запуска не нужны. `.env.example` содержит только пример конфигурации; настоящий
`.env` игнорируется Git. Не помещайте пароли EKT, ключи моделей или bootstrap-токен
в frontend, Git, URL репозитория либо документацию.

| Компонент | Адрес по умолчанию на локальной машине | Адрес внутри Docker |
| --- | --- | --- |
| Frontend | `http://localhost:5173` | `http://frontend:8080` |
| Assistant API / Swagger | `http://localhost:8000/docs` | `http://assistant-service:8000` |
| Catalog API | `http://localhost:8080/api/catalog/products?query=LED` | `http://ekt-catalog-service:8080` |
| Assistant worker | Отдельного публичного порта нет | Общая SQLite-база с Assistant API |

Браузер обращается к `/assistant/` на origin frontend; Nginx передаёт запросы
Assistant API. API сохраняет задания в SQLite, worker обрабатывает сообщения
и вложения, запрашивает Catalog API и при настройке модели генерирует ответ.
Только Catalog service использует Basic Auth для доступа к EKT.

В общем стеке включены live-каталог и production-режим Assistant. Гостевые сессии,
синтетическая подмена каталога и операции корзины отключены. Пользователь
регистрируется или входит через frontend. Локальные аккаунты ещё не связаны
с аккаунтами и корзиной сайта EKT. Независимый деморежим описан ниже в разделе
[локальной разработки](#локальная-разработка-и-проверки).

## Развёртывание на Ubuntu

Основа инструкции — [deploy.md](deploy.md). Установите Docker Engine и Compose plugin
по [официальной инструкции для Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
Если репозитория ещё нет, клонируйте его через настроенный Git-доступ:

```sh
git clone https://github.com/BAITC-Hacks/hack-e4fbf0e4-dairn.git
cd hack-e4fbf0e4-dairn
git branch --show-current
```

Перед сборкой выберите согласованную ветку развёртывания. Не считайте, что новые
изменения рабочей ветки уже включены в `main`. Для существующего checkout перейдите
в его фактический каталог и используйте команды обновления ниже.

Создайте `.env` и запустите стек командами из [быстрого старта](#запуск-всего-приложения).
Задайте `PUBLIC_FRONTEND_URL=http://SERVER_IP:5173` либо реальный origin домена,
без завершающего `/` и пути. В браузере используйте этот адрес, а не `localhost`
сервера. При изменении `FRONTEND_PORT` обновите порт и в `PUBLIC_FRONTEND_URL`.

На небольшом сервере можно последовательно собрать образы, чтобы снизить пиковое
потребление памяти. Assistant API и worker используют один образ:

```sh
docker compose config --quiet
docker compose build frontend
docker compose build assistant-service
docker compose build ekt-catalog-service
docker compose up -d --no-build --wait --wait-timeout 180
```

До запуска проверьте занятые порты. `FRONTEND_PORT`, `ASSISTANT_PORT` и `CATALOG_PORT`
меняют опубликованные порты хоста; внутренние Docker-адреса остаются прежними.
Например, `CATALOG_PORT=8081` освобождает конфликт с другим приложением на 8080.
Сервисные Compose-стеки не нужно запускать одновременно с корневым на тех же портах.

По умолчанию порты публикуются на всех IPv4-интерфейсах (`BIND_ADDRESS=0.0.0.0`).
Разрешите нужные TCP-порты в firewall сервера/провайдера. Docker-публикация портов
может обходить правила UFW; настройка firewall описана в инструкции Docker выше.
Для доступа только с хоста или через внешний reverse proxy используйте
`BIND_ADDRESS=127.0.0.1`. Compose сам не выпускает TLS-сертификаты: перед передачей
реальных учётных данных через Интернет настройте HTTPS на внешнем reverse proxy.
Прямой Catalog API пока не требует аутентификации.

### Проверка после запуска

При нестандартных портах замените их в командах:

```sh
curl --fail http://localhost:5173/health/live
curl --fail http://localhost:5173/assistant/health/live
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8080/health/ready
curl --fail 'http://localhost:8080/api/catalog/products?query=LED'
docker compose ps
docker compose logs --tail=100
```

`healthy` и `/health/ready` не подтверждают правильность credentials EKT или
доступность upstream: проверьте товарный запрос и `metadata` ответа. Пустой список
с охватом `PARTIAL` сам по себе не является ошибкой связи и не доказывает отсутствие
товара в полном каталоге. Затем откройте frontend, зарегистрируйтесь и отправьте
в чат артикул из полученного ответа. При настроенной модели естественный вопрос
должен вернуть `answer_mode: model`; точный артикул может обрабатываться быстрым
шаблоном без вызова модели.

Дополнительная проверка реального стека выполняет платные обращения к модели,
создаёт временные аккаунты/чаты и удаляет созданные ею данные:

```sh
docker compose exec -T -e LIVE_STACK_TEST=1 assistant-service python - \
  < assistant-service/tests/live_stack_smoke.py
```

Для неё нужны доступные EKT/OpenAI и товар с артикулом в результате поиска `LED`.
Это smoke-проверка, а не нагрузочный тест или гарантия p95 задержки.

### Обновление и данные

```sh
git status --short
git branch --show-current
git pull --ff-only
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
```

Сохраните локальные изменения до обновления; `--ff-only` останавливается при
расхождении веток. Существующий `.env` при обновлении не копируют заново из примера:
добавляйте только новые необходимые параметры. Изменение настроек требует
пересоздания контейнеров через `up -d`; изменения `VITE_CERTIFICATE_ORIGINS` требуют
также пересборки frontend. Для нового домена frontend пересобирать не нужно:
он использует proxy на своём origin.

Контейнеры автоматически перезапускаются, логи ротируются. SQLite и загрузки
Assistant находятся в `/data` общего named volume `assistant-data` (для проекта
`ekt` обычно `ekt_assistant-data`). Перед резервным копированием остановите **оба**
процесса — API и worker — и скопируйте весь `/data`, затем запустите их снова.
Храните резервную копию отдельно от Docker-хоста. Для отката сохраните ревизию,
образы и совместимую копию данных перед обновлением.

`docker compose down` сохраняет named volume; `docker compose down -v` удаляет
пользователей и историю вместе с ним. Смена имени Compose-проекта или переход
с отдельного Compose-файла сервиса на корневой может создать другой volume:
данные автоматически не мигрируют. Этот вариант рассчитан на один хост;
масштабирование API/worker требует отдельной проверки работы SQLite.

## Переменные окружения

Таблица описывает **все параметры, которые корневой Compose читает из `.env`**.
Значения по умолчанию сверены с [`.env.example`](.env.example) и
[docker-compose.yml](docker-compose.yml); параметры отдельных сервисов могут отличаться.
Секреты в примере оставлены пустыми.

| Переменная | Обязательность | По умолчанию | Назначение |
| --- | --- | --- | --- |
| `PUBLIC_FRONTEND_URL` | Указать для сервера | `http://localhost:5173` | Origin браузерного frontend без пути и завершающего `/`; задаёт разрешённый CORS origin и базу ссылок Assistant. |
| `BIND_ADDRESS` | Нет | `0.0.0.0` | Интерфейс для опубликованных портов; `127.0.0.1` ограничивает доступ хостом. |
| `FRONTEND_PORT` | Нет | `5173` | Порт frontend на хосте; согласовать с `PUBLIC_FRONTEND_URL`. |
| `ASSISTANT_PORT` | Нет | `8000` | Порт Assistant API на хосте. |
| `CATALOG_PORT` | Нет | `8080` | Порт Catalog API на хосте; Docker-взаимодействие остаётся на 8080. |
| `IMAGE_TAG` | Нет | `local` | Тег общего образа `ekt-assistant` для API и worker. |
| `EKT_API_BASE_URL` | Нет | `https://ekt.kz` | HTTPS origin источника EKT, без `/api`; используется Catalog service. |
| `EKT_API_USERNAME` | **Да** | Пусто | Логин Basic Auth партнёрского EKT API. Compose не запускается с пустым значением. |
| `EKT_API_PASSWORD` | **Да** | Пусто | Пароль Basic Auth партнёрского EKT API. Compose не запускается с пустым значением. |
| `CATALOG_MAX_PRODUCTS` | Нет | `100` | Максимум загружаемых товаров, от 1 до 1000; не подтверждает полный охват каталога. |
| `CATALOG_CACHE_TTL_SECONDS` | Нет | `60` | Срок кеша нормализованной выборки в секундах, от 1 до 3600. |
| `CATALOG_LOAD_TIMEOUT_MS` | Нет | `25000` | Общий таймаут загрузки каталога в миллисекундах, от 1 до 120000. |
| `ASSISTANT_CATALOG_TIMEOUT_SECONDS` | Нет | `30` | Таймаут HTTP-запроса Assistant к Catalog, больше 0 и не больше 30 секунд. Согласуйте с таймаутом загрузки. |
| `ASSISTANT_MODEL_API_KEY` | Для живых AI-ответов | Пусто | Ключ OpenAI только для Assistant; без ключа используются ответы-шаблоны по данным каталога. |
| `ASSISTANT_MODEL_NAME` | Если задан ключ Assistant | Пусто | Явное имя модели Assistant; автоматического выбора модели нет. |
| `ASSISTANT_BOOTSTRAP_TOKEN` | Нет | Пусто | Секрет для доверенного website backend; регистрация и вход пользователей работают без него. Во frontend не передавать. |
| `ASSISTANT_AUTH_TOKEN_TTL_SECONDS` | Нет | `86400` | Срок account bearer token в секундах, от 60 до 2592000; logout отзывает текущий токен. |
| `ASSISTANT_USER_HISTORY_TTL_DAYS` | Нет | `30` | Срок хранения чата пользователя от создания, от 1 до 365 дней; не продлевает срок хранения вложений. |
| `OPENAI_SEARCH_ENABLED` | Нет | `false` | Включает отдельный AI-поиск кандидатов в Catalog API; обычный GET-поиск не зависит от этого флага. |
| `OPENAI_PREVALIDATION_ENABLED` | Нет | `false` | Флаг отдельной AI-предвалидации; не включает AI-поиск и не подключает её автоматически ко всему pipeline. |
| `OPENAI_API_KEY` | Для AI-функций каталога | Пусто | Ключ OpenAI для Catalog service; независим от `ASSISTANT_MODEL_API_KEY`. |
| `OPENAI_MODEL` | Для AI-функций каталога | Пусто | Явная модель Catalog AI; независима от модели Assistant. |
| `OPENAI_TIMEOUT_MS` | Нет | `20000` | Таймаут AI-запроса Catalog в миллисекундах, от 1 до 120000. |
| `OPENAI_MAX_OUTPUT_TOKENS` | Нет | `2048` | Ограничение токенов ответа Catalog AI, от 256 до 8192. |
| `VITE_CERTIFICATE_ORIGINS` | Нет | Пусто | Дополнительные доверенные origin ссылок сертификатов через запятую. Публичный build-параметр; после изменения пересобрать frontend. |

Два набора ключей модели относятся к разным микросервисам. Настройка Assistant AI
не включает Catalog AI, и наоборот. Для обычного чата с поиском достаточно ключа
и модели Assistant; отдельный AI-поиск каталога по умолчанию выключен.

### Настройки, заданные самим Compose

Добавление произвольной переменной в корневой `.env` **не передаёт её автоматически
в контейнер**. Например, эти настройки зафиксированы в Compose или получаются
из других переменных:

| Настройка | Значение в общем стеке |
| --- | --- |
| `ASSISTANT_ENVIRONMENT`, `ASSISTANT_ALLOW_DEMO_SESSIONS` | `production`, `false` |
| `ASSISTANT_CATALOG_MODE`, `ASSISTANT_CATALOG_BASE_URL` | `http`, `http://ekt-catalog-service:8080` |
| `ASSISTANT_CATALOG_MOCK_ON_UNAVAILABLE`, `ASSISTANT_CART_MODE` | `false`, `disabled` |
| `ASSISTANT_DATA_DIR`, `ASSISTANT_POLICY_FILE` | `/data`, `/config/policies.json` |
| `ASSISTANT_FRONTEND_BASE_URL`, `ASSISTANT_CORS_ORIGINS` | Формируются из `PUBLIC_FRONTEND_URL`. |
| `CATALOG_SOURCE`, `CATALOG_HOST`, `PORT` | `live`, `0.0.0.0`, `8080` |
| `CATALOG_CORS_ORIGINS` | Формируется из `PUBLIC_FRONTEND_URL`. |
| `VITE_ASSISTANT_API_URL` | `/assistant` при сборке frontend. |

`CATALOG_MAX_PAGES` не передаётся корневым Compose; действует значение JVM по
умолчанию — 10. Дополнительные параметры Python/JVM, например
`ASSISTANT_MODEL_TIMEOUT_SECONDS` или `CATALOG_MAX_PAGES`, требуют изменения
`environment` в Compose/override либо самостоятельного запуска сервиса.
Они не начнут действовать только от добавления строки в корневой `.env`.

## Быстрый старт каталога без credentials

Нужен JDK 21. Gradle 8.8 закреплён в wrapper; при первой сборке нужен доступ
к дистрибутиву Gradle и зависимостям. Из корня репозитория:

```sh
cd ekt-catalog-service
sh ./gradlew --no-daemon test serverDist
python3 scripts/verify-local.py
```

Для HTTP-проверки нужен Python 3. Скрипт временно запускает собранный JAR,
проверяет API на сохранённом образце и обработку ошибок, затем останавливает сервер.
Чтобы оставить сервер запущенным:

```sh
# Из ekt-catalog-service/
CATALOG_SOURCE=snapshot \
CATALOG_SNAPSHOT_PATH=src/test/resources/ekt/products-page-1.json \
sh ./gradlew runServer
```

В другом терминале:

```sh
curl -i 'http://127.0.0.1:8080/health/live'
curl -i 'http://127.0.0.1:8080/api/catalog/products/45357'
curl -i 'http://127.0.0.1:8080/api/catalog/products?query=310100080_'
```

Это офлайн-запуск на сохранённой странице из 20 товаров. Он не подтверждает
доступность EKT или актуальность цен. Задача `runServer` запускает HTTP-сервис,
а `run` — CLI. Для запуска собранного JAR сохраняйте рядом каталог `build/server/lib/`.

## Возможности Catalog API

| Метод и маршрут | Текущее поведение |
| --- | --- |
| `GET /api/catalog/products/{id}` | Краткая карточка из загруженных страниц списка |
| `GET /api/catalog/products?query={query}` | Поиск по артикулу и названию в загруженной выборке |
| `GET /api/catalog/products/{id}/availability` | Наличие `UNKNOWN`, количество `null` для изученной схемы |
| `GET /api/catalog/products/{id}/analogs` | HTTP 422 для загруженного товара: недостаточно проверенных данных |
| `POST /api/catalog/assist/search` | Опциональный разбор текста и предложение кандидатов через OpenAI |
| `GET /health/live` | Проверка доступности процесса |
| `GET /health/ready` | Проверка наличия настроенного адаптера; не проверяет upstream |

`id` и артикул — разные значения: для артикула используйте `query`.
Поиск не учитывает регистр, точное совпадение артикула идёт первым.
Узкие подсказки для запросов «автомат» и «дифавтомат» учитывают сокращения
`АВ DRX…` и `Диф.авт.` в названиях. Это не проверка технической совместимости.

Ответ поиска содержит `items`, `matchedProducts`, `warnings` и `metadata`.
Предупреждение `PARTIAL_CATALOG_SEARCH` возвращается и при найденных совпадениях.
Пустой результат не доказывает отсутствие товара во всём каталоге; отсутствующий
в выборке ID возвращает `PRODUCT_NOT_IN_LOADED_SAMPLE`. Ошибка источника
возвращается явно, а не превращается в успешный пустой список.

Полный контракт, примеры JSON и коды ошибок — в [docs/API.md](docs/API.md).

## Источники и конфигурация каталога

При самостоятельном запуске JVM источник по умолчанию выключен (`CATALOG_SOURCE=disabled`).
Режим `snapshot` читает одну сохранённую страницу без сети. Режим `live` требует
`EKT_API_BASE_URL` (HTTPS origin без `/api`), `EKT_API_USERNAME` и `EKT_API_PASSWORD`.
При сбое live-источника автоматической подмены на snapshot нет.

Live-адаптер последовательно читает страницы начиная с первой. Загрузка ограничена
числом товаров, страниц и общим таймаутом; пустая страница завершает обход.
По умолчанию `CATALOG_MAX_PRODUCTS=100`, `CATALOG_MAX_PAGES=10`,
`CATALOG_LOAD_TIMEOUT_MS=35000`, `CATALOG_CACHE_TTL_SECONDS=60`.
Корневой Compose задаёт некоторые значения отдельно. Загрузка выполняется лениво,
результат кешируется; ошибки страниц отклоняют всю загрузку.

Охват всегда `PARTIAL`, общее число товаров неизвестно (`totalProducts=null`).
Ограниченная пагинация проверена синтетическими тестами; поведение следующих
страниц реального EKT ещё требует проверки. Для snapshot актуальность неизвестна;
время live-загрузки не гарантирует актуальность коммерческих данных поставщика.

Самостоятельный сервер слушает `127.0.0.1:8080`; адрес задаётся через `CATALOG_HOST`,
порт — через `PORT` или `CATALOG_PORT` (`PORT` имеет приоритет).
Compose загружает `.env`, JVM и CLI автоматически его не читают.
Credentials и ключи моделей должны оставаться в серверном окружении, вне Git
и конфигурации frontend. Все параметры — в [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## AI-поиск и ограничения данных

AI-поиск выключен по умолчанию. Для включения нужны `OPENAI_SEARCH_ENABLED=true`,
`OPENAI_API_KEY` и явно выбранная `OPENAI_MODEL`. Обычный GET-поиск не зависит от OpenAI.
Флаг `OPENAI_PREVALIDATION_ENABLED` управляет отдельной функцией и не включает поиск.

Сервис выполняет до двух AI-вызовов, рассматривает до 20 товаров и возвращает
до пяти кандидатов. Товарные факты берутся из нормализованного каталога;
модель не получает credentials и raw EKT JSON. Результат содержит
`verifiedAnalogs=false`, `compatibility=UNVERIFIED`, `requirementsVerified=false`.
Живая проверка именно этого сценария Catalog API в документации не подтверждена.

Изученный образец списка не подтверждает валюту, наличие, количество, склады,
сертификаты и структурированные характеристики. Отсутствующая цена остаётся `null`,
сумма передаётся точной десятичной строкой, неизвестная валюта не заменяется на KZT.
Пустой `offers` и фильтр сайта «В наличии» не доказывают численный остаток.
Описание товара нужно хранить отдельно от проверенных характеристик.

Для настоящего подбора аналогов остаётся проверить detail endpoint, параметры
совместимости и актуальное наличие. Внешнее развёртывание каталога, HTTPS,
живые запросы EKT и откат на целевом хосте требуют отдельной проверки;
локальный smoke-test не подтверждает готовность production.

## Assistant API и пользовательские данные

Assistant предоставляет регистрацию, вход, logout, профиль, список чатов,
сообщения/историю, загрузки, polling и SSE. Аккаунтный bearer token открывает только
чаты своего пользователя; учётные записи и история сохраняются в SQLite между
перезапусками. Подробные маршруты и примеры — в
[AUTHENTICATION.md](assistant-service/AUTHENTICATION.md),
[FRONTEND_AGENT.md](assistant-service/FRONTEND_AGENT.md) и
[OpenAPI](assistant-service/openapi.json). Для ручной проверки доступна
[Postman-коллекция](assistant-service/postman/EKT-Assistant.postman_collection.json).

Поддерживаются Excel (`.xlsx`, `.xls`), Word (`.docx`, `.doc`), PDF, JPEG/JPG и PNG.
Лимит файла — 10 MiB; фото и сканы обрабатываются OCR, распознавание предметов без
читаемой маркировки не реализовано. Бинарные файлы удаляются после обработки;
извлечённые данные живут не более 24 часов. История пользователя по умолчанию
хранится 30 дней, гостевой чат в отдельном demo-режиме — не более 24 часов.
Текст вложения, процитированный в ответе, следует сроку хранения сообщения.

POST сообщения ждёт до 1,5 секунды, затем при незавершённой обработке возвращает
202 со ссылками polling/SSE. Это срок подтверждения приёма, а не обещание готового
ответа за 1,5 секунды. SSE передаёт состояния и готовый результат, не отдельные
токены модели. Точные SKU могут отвечать без модели; остальные запросы используют
до одного вызова генерации ответа Assistant. При ошибке модели есть шаблонный
ответ на основании каталога. RAG пока не включён; предусмотрен интерфейс
`KnowledgeProvider` для будущего поиска по знаниям.

Подтверждённые условия оплаты, доставки и минимальной партии задаются в
[assistant-service/config/policies.json](assistant-service/config/policies.json)
объектами `id`, `text`, `source`, `version`. Пустой файл означает отсутствие
подтверждённых условий. После изменения перезапустите worker.
Синтетическая demo-корзина требует явного подтверждения; она не резервирует
остатки EKT и не оформляет реальные заказы.

## Локальная разработка и проверки

Отдельные Compose-файлы предназначены для независимой разработки; их настройки
и volumes отличаются от общего production-стека.

### Assistant: demo без внешнего каталога

Из корня репозитория, на свободных портах:

```sh
umask 077
if [ ! -f assistant-service/.env ]; then
  cp assistant-service/.env.example assistant-service/.env
fi
chmod 600 assistant-service/.env
docker compose --env-file assistant-service/.env -f assistant-service/compose.yaml up -d --build --wait
```

Настройки по умолчанию — development, синтетический каталог и demo-корзина.
Примеры артикулов: `DEMO-C16`, `DEMO-C16-OLD`, `DEMO-C16-ALT`.
Подключение HTTP Catalog и явная тестовая подмена при ошибке соединения описаны
в [CATALOG_INTEGRATION.md](assistant-service/CATALOG_INTEGRATION.md).
Такую подмену нельзя включить в production. Partner Basic Auth настраивается
в Catalog service, а не в Assistant.

Для запуска без Docker нужны Python 3.12+, Tesseract с `rus+eng`, Poppler
(`pdftoppm`) и LibreOffice Writer. Docker-образ устанавливает их сам.

```sh
cd assistant-service
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
# Терминал 1:
.venv/bin/uvicorn app.main:app --reload --port 8000
# Терминал 2, тот же каталог данных и окружение:
.venv/bin/python -m app.worker
# Проверки:
.venv/bin/python -m pytest -q
```

Локальный Python читает экспортированные `ASSISTANT_*`, но автоматически не
загружает `.env`. Один API без worker не завершит обработку сообщений и файлов.
Контейнерная проверка OCR/Office/HTTP использует временные данные без живой модели
и выполняется из корня после сборки образа:

```sh
docker compose -f assistant-service/compose.yaml run --rm --no-deps -T \
  -v "$PWD/assistant-service/tests:/checks:ro" \
  assistant-service python /checks/container_smoke.py
```

### Frontend

Для разработки используйте Node.js 24; Docker устанавливает его сам.

```sh
cd frontend-service
npm ci
npm run dev
# Проверки типов, стиля, unit-тестов и production-сборки:
npm run check
# Детерминированные браузерные тесты:
npx playwright install chromium
npm run test:e2e
```

При самостоятельной разработке [frontend-service/.env.example](frontend-service/.env.example)
задаёт публичные параметры, включая `VITE_ASSISTANT_API_URL` (по умолчанию
`http://localhost:8000`). Backend должен разрешать origin frontend в CORS.
Корневой Compose вместо прямого API URL собирает `/assistant` и использует Nginx;
сервисный Compose запускает Vite preview только для локальной проверки.

Docker-проверки из `frontend-service/`:

```sh
docker compose run --build --rm frontend-test
docker compose run --build --rm frontend-e2e
```

Браузерные тесты с API fixtures не подтверждают живую интеграцию с EKT/OpenAI.
Интерфейс поддерживает RU/KZ; это перевод UI, а не текстов товаров или ответов API.
Backend пока принимает `locale: "ru"`. Правила frontend — в
[react-standards.md](frontend-service/react-standards.md).

## CLI каталога

CLI и HTTP-сервер имеют разные точки входа: `run` запускает CLI, `runServer` — Ktor.
Из каталога `ekt-catalog-service/`:

```sh
sh ./gradlew --quiet installDist
bash bin/ekt-cli --help
bash bin/ekt-cli list --page 1 --output local-evidence/products-page-1.json
bash bin/ekt-cli list --page 2 --output local-evidence/products-page-2.json
# Вместо ID подставьте идентификатор из списка товаров:
bash bin/ekt-cli detail --id ID --output local-evidence/product-detail.json
```

Запускник запрашивает логин и скрытый пароль, если они не экспортированы в
окружение; по умолчанию адрес источника — `https://ekt.kz`. Сам JVM/CLI `.env`
не читает. Не передавайте пароль аргументом команды. Для неинтерактивного запуска
заранее задайте `EKT_API_BASE_URL`, `EKT_API_USERNAME`, `EKT_API_PASSWORD` в окружении.

`list` вызывает upstream `/api/products`, `--page` добавляет номер страницы,
`detail --id` обращается к `/api/products/detail?id=...`. Это raw-экспорт для
исследования, а не нормализованный контракт Catalog API. `--output` не заменяет
существующий файл: выбирайте новый путь для каждого наблюдения. Успешный JSON
без `--output` выводится в stdout, диагностика — в stderr. Каталог `local-evidence/`
игнорируется Git; перед публикацией данных проверьте отсутствие секретов.

Коды выхода дистрибутива CLI: `0` — успех/справка, `2` — аргументы или конфигурация,
`3` — EKT/сеть/таймаут/JSON, `4` — ошибка экспорта или существующий файл,
`1` — непредвиденная ошибка. Gradle может заменить ненулевой код дочернего процесса
собственным кодом 1; для автоматизации используйте запускник или установленный
дистрибутив, а не `gradlew run`.

## Документация

- [Авторизация и история](assistant-service/AUTHENTICATION.md) — пользователи, токены, владение чатами и сроки хранения.
- [Frontend ↔ Assistant](assistant-service/FRONTEND_AGENT.md) — HTTP-контракт, загрузки, SSE и обработка ошибок.
- [Assistant ↔ Catalog](assistant-service/CATALOG_INTEGRATION.md) — структуры данных и тестовый fallback.
- [Catalog API](docs/API.md) — маршруты, JSON-контракт, поиск, пагинация, кеш и ошибки.
- [Данные EKT](docs/EKT_DATA.md) — происхождение образца, наблюдаемая схема и план проверки API.
- [AI-поиск](docs/AI_SEARCH.md) — протокол поиска кандидатов, запуск, статусы и ограничения.
- [Развёртывание каталога](docs/DEPLOYMENT.md) — конфигурация, JAR, Docker, health, smoke и rollback; запись результатов локальной проверки.
- [Комментарии по документации](docs/WORK_COMMENTS.md) — ограничения достоверности данных и открытые вопросы.
- [Развёртывание приложения](deploy.md) — общий Compose для frontend, каталога, ассистента и worker.

Записи о выполненных проверках относятся к указанным в документах ревизиям и датам;
они не заменяют проверку текущей сборки или целевого окружения.
