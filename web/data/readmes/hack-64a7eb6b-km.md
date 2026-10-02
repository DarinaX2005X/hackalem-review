# HACKALEM.AI

«Аким на 5 часов» — учебный AI-симулятор управления городом с GIS-картой Астаны. Выберите пять решений для пяти районов учебного сценария, распределите 100 единиц бюджета и сравните последствия через восемь кварталов. Расчёты и сохранение сценариев работают без AI; агент объясняет результаты и предлагает изменения, которые применяются только после подтверждения пользователя.

**Демо доступно по ссылке: [ha-demo.5n.kz](https://ha-demo.5n.kz).**

**Стек:** PHP 8.4+, Laravel 13, PostgreSQL 18 с PostGIS, React 19, Inertia 3, TypeScript, Tailwind 4, Filament 5, Vite 8 / Vite+. Laravel AI SDK управляет обращениями к моделям и инструментам; Laravel Boost предоставляет инструменты разработчикам.

## Требования

- PHP 8.4+ с `pdo_pgsql`, `intl`, `bcmath`, `mbstring`, `dom`, `xml`, `zip`, `gd`, `pcntl`, `curl`, `openssl`, `zlib`. Для Windows используйте WSL2: процессы очередей требуют `pcntl`.
- Composer 2, Node.js 22.12+ и npm. Версии зависимостей зафиксированы в `composer.lock` и `package-lock.json`.
- PostgreSQL 18 и установленный для этой версии сервера PostGIS. Расширение нужно в обеих базах: `hackalem` и `hackalem_testing`. Локальное окружение проверено с PostGIS 3.6.
- Доступ на запись в `storage/` и `bootstrap/cache/`; свободное место для PostgreSQL и GIS-файлов в `storage/app/private/gis/`.

Очереди, сессии и кэш по умолчанию хранятся в PostgreSQL. Redis для стандартного запуска не нужен. Установка зависимостей требует интернета; комплектный GIS-архив импортируется без запросов к внешнему GIS API.

## Первая установка

```bash
git clone https://github.com/BAITC-Hacks/hack-64a7eb6b-km.git hackalem
cd hackalem

# Один раз, после установки и запуска PostgreSQL с PostGIS.
createdb -h 127.0.0.1 -U postgres hackalem
createdb -h 127.0.0.1 -U postgres hackalem_testing
psql -h 127.0.0.1 -U postgres -d hackalem -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
psql -h 127.0.0.1 -U postgres -d hackalem_testing -c 'CREATE EXTENSION IF NOT EXISTS postgis;'

# Только для новой установки: не перезаписывайте существующий .env.
cp .env.example .env
```

Перед следующей командой настройте `.env`: параметры `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` должны соответствовать вашим базам и пользователю. Команды выше предполагают локального пользователя `postgres`; при другом пользователе измените `-U` и назначьте ему необходимые права на базы. GIS-миграция также выполняет `CREATE EXTENSION IF NOT EXISTS postgis`: установите расширение заранее с правами администратора либо обеспечьте эти права пользователю миграций.

Для первого запуска без обращений к моделям задайте:

```dotenv
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000
SERVER_PORT=8000
DEMO_ADMIN_ENABLED=true

DB_CONNECTION=pgsql
QUEUE_CONNECTION=database
DB_QUEUE_RETRY_AFTER=240
CACHE_STORE=database
SESSION_DRIVER=database

AGENT_DRIVER=demo
OPENAI_API_KEY=
```

В `.env.example` указан `AGENT_DRIVER=auto`: он включает реальный AI при наличии ключа выбранного провайдера. `demo` принудительно оставляет локальный режим, даже если ключ уже задан.

```bash
composer setup
php artisan app:doctor --no-interaction
composer dev
```

`composer setup` выполняет `composer install`, создаёт `.env`, если его нет, вызывает `app:prepare`, затем `npm ci` и `npm run build`. `app:prepare`:

1. Создаёт `APP_KEY`, только если ключ ещё не задан.
2. Применяет миграции без очистки базы.
3. Создаёт локальные демо-учётные записи при включённом `DEMO_ADMIN_ENABLED`.
4. Загружает учебный датасет `astana-v1` и комплектный GIS-архив.

`app:prepare` разрешён только в `local` / `testing`. Существующий ключ и сохранённые сценарии остаются на месте. Повторная загрузка GIS seed пропускается, если в базе уже есть общие GIS-слои. Не используйте `migrate:fresh` для обновления базы приложения.

## Локальный запуск

`composer dev` запускает пять процессов и останавливает остальные, если один из них завершился:

| Процесс                                                                      | Назначение                                   |
| ---------------------------------------------------------------------------- | -------------------------------------------- |
| `php artisan serve --host=127.0.0.1`                                         | Laravel HTTP-сервер                          |
| `php artisan queue:work --queue=agents,default --tries=1 --timeout=180`      | AI- и демо-задачи, очередь `default`         |
| `php artisan queue:listen --queue=gis --tries=4 --timeout=190 --memory=1024` | Импорт GIS в отдельном процессе              |
| `php artisan schedule:work`                                                  | Планировщик                                  |
| `npm run dev -- --host=127.0.0.1`                                            | Vite, обновление frontend и SSR в разработке |

По умолчанию приложение открывается на `http://localhost:8000`. Если порт занят, задайте одинаковый порт в `APP_URL` и `SERVER_PORT`, например `8007`, и перезапустите `composer dev`. Vite использует локальный HTTP без автоматического сертификата Herd. Отдельный `inertia:start-ssr` в режиме разработки не требуется.

Если HTTP-сервер уже предоставляет Herd или другой сервер, запустите оставшиеся четыре команды из таблицы в отдельных терминалах. Простого `php artisan serve` недостаточно для обработки очередей и расписания.

| Путь                | Что открывается                                               |
| ------------------- | ------------------------------------------------------------- |
| `/` или `/login`    | Вход                                                          |
| `/map`              | Карта и симулятор; сюда перенаправляет после входа            |
| `/scenarios`        | Сохранённые сценарии                                          |
| `/scenarios/create` | Создание сценария                                             |
| `/dashboard`        | Список сценариев                                              |
| `/admin`            | Filament: управление доступом и просмотр запусков и сценариев |

Пользовательские страницы требуют входа и подтверждённого email. Отдельной страницы GET `/runs` сейчас нет: AI-запуски отображаются в сценариях и на карте.

## Вход и права

При `APP_ENV=local` и `DEMO_ADMIN_ENABLED=true` подготовка проекта создаёт три учётные записи с подтверждённым email:

| Роль                        | Email                   | Пароль    | Права по умолчанию                                                      |
| --------------------------- | ----------------------- | --------- | ----------------------------------------------------------------------- |
| `super_admin`               | `admin@hackalem.test`   | `admin`   | Пользовательское приложение и Filament                                  |
| Аналитик                    | `analyst@hackalem.test` | `analyst` | Просмотр, без создания запусков и подтверждения изменений               |
| Аким (Городской управленец) | `akim@hackalem.test`    | `akim`    | Создание сценариев и запусков, отмена и подтверждение своих предложений |

Это **локальные** демо-данные. Подсказки на странице входа отображаются только для доступных учётных записей с исходными паролями. `db:seed` повторно создаёт недостающие демо-записи; существующие аккаунты аналитика и акима не перезаписываются. Демо-администратор восстанавливает исходный пароль и роль также при открытии `/admin/login`.

`DEMO_ADMIN_ENABLED=false` отключает автоматическое создание и подсказки, но не удаляет уже созданные аккаунты. В `production` создание демо-пользователей и подсказки выключены независимо от флага; существующие записи при этом также сохраняются.

Для личной локальной учётной записи есть интерактивная команда со скрытым вводом пароля от 12 символов:

```bash
php artisan app:user developer@example.test --name=Developer --admin
```

Без `--admin` назначается роль акима. Команда работает только при `APP_ENV=local`. Обычная регистрация тоже доступна; при `MAIL_MAILER=log` ссылки подтверждения email находятся в `storage/logs/laravel.log`.

В Filament допускается только `super_admin` с подтверждённым email. Пользователей и роли можно редактировать, а запуски и снимки сценариев доступны только для просмотра. Системная роль и демо-администратор защищены; последнего супер-администратора нельзя удалить или лишить доступа. Новым пользователям назначается роль акима. Права проверяются сервером: даже `super_admin` не получает доступ к чужим сценариям и предложениям через пользовательские маршруты.

## Очереди и расписание

Для стандартной конфигурации оставьте `QUEUE_CONNECTION=database` и `DB_QUEUE_RETRY_AFTER=240`. Значение `retry_after` должно быть больше всех таймаутов задач и процессов: AI job — 180 секунд, GIS job — 170 секунд, GIS listener — 190 секунд. `app:doctor` проверяет порог только относительно 180 секунд; не уменьшайте интервал до значения ниже GIS-таймаута.

AI- и демо-запуски используют одну очередь `agents`. Без её worker задача останется в `queued`. Автоматические повторы AI отключены (`tries=1`); повтор через интерфейс создаёт новый запуск. Не используйте массовый `queue:retry all` для повторения AI-запусков: завершённая задача повторно не исполняется. GIS допускает до четырёх попыток при временных сетевых сбоях, с задержками 15, 60 и 180 секунд.

Расписание находится в `routes/console.php`:

- Каждую минуту `agents:expire-runs` завершает ошибкой запуски в `running` старше пяти минут и в `queued` старше часа.
- Ежедневно в **03:00 по Asia/Almaty** `gis:sync` обнаруживает внешние слои и ставит их импорт в очередь `gis`. `schedule:list` может показывать время в часовом поясе приложения.

После изменения PHP-кода или конфигурации перезапустите процессы. Для локального `composer dev` проще остановить его через Ctrl+C, при изменении `.env` выполнить `php artisan config:clear --no-interaction`, затем снова запустить `composer dev`. Команда `queue:restart` завершает постоянные workers после текущей задачи; сама она новые процессы не запускает. В связке `concurrently --kill-others` завершение worker остановит и остальные процессы.

Диагностика без обработки задач:

```bash
php artisan app:doctor --no-interaction
php artisan migrate:status --no-interaction
php artisan schedule:list --no-interaction
php artisan queue:failed --no-interaction
php artisan gis:status --no-interaction
```

Ошибки AI смотрите также в карточке запуска и `storage/logs/laravel.log`: runtime фиксирует неудачный запуск сам, поэтому запись не обязательно появится в `queue:failed`. `app:doctor` не вызывает AI и не проверяет доступность всех внешних GIS-источников или полноту архива.

## GIS-данные

Комплектный архив находится в `database/seeders/data/gis-astana/`. `GisDatasetSeeder` проверяет целостность файлов и восстанавливает объекты в PostgreSQL, а файлы карты — в `storage/app/private/gis/blobs/`. Повторная установка сохраняет существующий общий архив. `GIS_SEED_ENABLED=false` позволяет пропустить загрузку GIS seed.

Компактный seed ограничен 50 МБ: он содержит выбранные слои и базовые векторные тайлы до zoom 13, а не полную копию внешнего портала. Слои могут иметь состояния `seeded` или `not_seeded`; отсутствие объекта в неполном снимке не означает его удаления. Полноту и версии показывает `gis:status --json`. Учебные показатели пяти районов синтетические и не заменяют географические данные GIS.

Для обновления из внешнего источника нужен интернет и работающий процесс очереди `gis`:

```bash
# Новый импорт обнаруженных слоёв.
php artisan gis:sync --no-interaction

# Продолжить незавершённый импорт, включая слои с ошибками.
php artisan gis:sync --resume --no-interaction

# Импортировать только векторные и табличные слои.
php artisan gis:sync --vectors --no-interaction

php artisan gis:status --json --no-interaction
```

Это отдельные варианты запуска: не выполняйте все три команды синхронизации подряд без необходимости. `gis:sync` ставит задания в очередь, а не ждёт окончания загрузки. Полный архив, особенно растры и подробные тайлы, может занимать существенно больше места, чем seed. История внешних данных начинается с первого наблюдения.

Экспорт переносимого seed выполняется в **новый, ещё не существующий каталог**:

```bash
php artisan gis:seed-export --path=/tmp/hackalem-gis-seed --no-interaction
```

По умолчанию экспорт компактный; `--full` включает полный архив. Для фиксации скачанных частей незавершённого импорта предусмотрен `--freeze-incomplete`: сначала остановите GIS workers и исключите запуск новой синхронизации. Эта опция меняет состояние неполных версий в базе.

## AI: демо и реальный провайдер

| `AGENT_DRIVER` | Поведение                                                                          |
| -------------- | ---------------------------------------------------------------------------------- |
| `demo`         | Локальные ответы и настоящие инструменты приложения без вызовов моделей            |
| `auto`         | AI при непустом ключе выбранного провайдера, иначе демо; значение в `.env.example` |
| `laravel`      | Обязательный реальный провайдер; отсутствие ключа считается ошибкой                |

Демо использует PostgreSQL, очередь, расчёты, журнал и подтверждения. Оно объясняет бюджет, районы, риски, сроки эффекта и синергии, сравнивает варианты и учитывает последние шесть успешных пар сообщений сценария. Свободный диалог с языковой моделью оно не заменяет.

Для реального AI добавьте ключ только в игнорируемый `.env` или хранилище секретов окружения. Не публикуйте его в Git, логах или сообщениях. Настройки провайдера по умолчанию:

```dotenv
AGENT_DRIVER=auto
AGENT_PROVIDER=openai
AGENT_MODEL=gpt-5.4-nano
```

Ключ задаётся переменной `OPENAI_API_KEY`. Модель должна быть доступна вашему аккаунту и поддерживать инструменты. Другие провайдеры настраиваются в `config/ai.php`.

После изменения режима, модели или ключа очистите локальный кэш конфигурации, выполните `app:doctor` и перезапустите процессы. В production пересоберите `config:cache` и перезапустите workers через менеджер процессов.

Режим, провайдер, модель, версия prompt и лимиты сохраняются при постановке задачи. Старый демо-запуск не станет платным после добавления ключа. Принудительный `demo` блокирует выполнение ранее поставленных live-задач; удаление ключа приводит к ошибке уже поставленного live-запуска. Ошибки ключа, квоты и соединения не подменяются демо.

Лимиты из `config/agents.php`:

| Переменная             | По умолчанию | Допустимые границы                             |
| ---------------------- | ------------ | ---------------------------------------------- |
| `AGENT_MAX_STEPS`      | 5            | 1–10                                           |
| `AGENT_MAX_TOKENS`     | 2048         | 128–8192 выходных токенов на один вызов модели |
| `AGENT_MAX_TOOL_CALLS` | 8            | 1–20                                           |
| `AGENT_TIMEOUT`        | 120          | 10–150 секунд на запрос                        |

Эти ограничения не являются денежным бюджетом. Одновременно допускаются до трёх активных запусков на пользователя, не более одного разбора и одного диалога на сценарий. Любое предложение записи проходит через `ToolBroker` и отдельное подтверждение владельца после успешного завершения запуска. Отменённый или неуспешный запуск не может применить предложение.

## Проверка городского сценария

1. Войдите как аким или администратор, откройте `/scenarios` → «Новый сценарий» → «Пример из задания».
2. Проверьте расчёт: Score **56,54307**, расходы **95**. Исходный Score города — **52,55768**; интерфейс может округлять отображение.
3. Сохраните сценарий: расчёт, матрица показателей, синергии и до трёх лучших замен доступны сразу, независимо от AI.
4. Нажмите «Получить разбор». Затем спросите: «Как распределён бюджет?», «Покажи варианты улучшения», «Сравни второй вариант», «Подготовь его».
5. Проверьте пять решений и Score в предложении. «Создать этот вариант» сохраняет отдельный сценарий; «Отклонить» оставляет исходный.
6. Сравните два сценария одной версии датасета и калькулятора.

Сервер проверяет ровно пять разных мер, максимум две в направлении, бюджет ≤100, корректность районов и несовместимости. Неиспользованный бюджет бонуса не даёт. Расчёт ведётся с точностью BCMath; AI не определяет итоговый Score.

## Обновление существующей локальной установки

Сделайте резервную копию PostgreSQL и `storage/app/private/gis/`, остановите `composer dev`, получите нужную версию кода и выполните из корня проекта:

```bash
composer install --no-interaction
npm ci
php artisan config:clear --no-interaction
php artisan app:prepare --no-interaction
npm run build
php artisan app:doctor --no-interaction
composer dev
```

Сохраняйте `.env` и `APP_KEY`; не копируйте `.env.example` поверх своей конфигурации. Новые переменные переносите вручную. `app:prepare` применяет миграции и seed без очистки базы; для загрузки только учебного датасета есть `php artisan db:seed --class=SimulationDatasetSeeder --no-interaction`. Существующая версия `astana-v1` не перезаписывается — изменения данных оформляются новой версией.

## Тесты и проверки

Тестам нужна отдельная PostgreSQL-база `hackalem_testing` с PostGIS. При необходимости скопируйте `.env.testing.example` в `.env.testing`, настройте подключение и локальный `APP_KEY`. PHPUnit принудительно задаёт имя тестовой базы, `AGENT_DRIVER=demo`, пустой `OPENAI_API_KEY` и отключает автоматический GIS seed. Базовый `TestCase` проверяет имя базы до её очистки и запрещает непредусмотренные HTTP-запросы. Не запускайте несколько наборов тестов одновременно против одной базы.

```bash
composer test:agents        # AgentRuntimeTest: жизненный цикл, инструменты, approvals
php artisan test --compact --filter='SimulationCalculationTest|SimulationScenarioTest|ScenarioAiTest' --no-interaction
php artisan test --compact --filter=Gis --no-interaction
composer test              # Весь PHP-набор на PostgreSQL
composer types:check       # Larastan, level 7

php artisan wayfinder:generate --with-form --no-interaction
npm run types:check
npm run check              # Frontend lint и форматирование
npm run test:simulator

composer ci:check          # Pint, Larastan, frontend checks, PHP-тесты и production build
git diff --check
```

Полная проверка комплектного GIS-архива включается отдельно; обычный прогон её пропускает:

```bash
GIS_VERIFY_SEED=true php artisan test --compact --filter=test_bundled_dataset --no-interaction
```

SDK-тесты используют `fake()->preventStrayPrompts()` и не вызывают платные API. Fake не исполняет цикл инструментов: `ToolBroker` и подтверждения проверяются отдельно. Сгенерированные `resources/js/actions`, `resources/js/routes` и `resources/js/wayfinder` не редактируются вручную; их создают Wayfinder, сборка и `composer ci:check`.

В `.github/workflows/tests.yml` настроен `composer ci:check` с PostgreSQL 18. Для GIS-тестов CI также нужен PostGIS: в текущем workflow указан образ `postgres:18` без отдельного шага установки расширения; это окружение необходимо дополнить PostGIS перед запуском GIS-миграций.

## Запуск на сервере

`composer setup`, `app:prepare` и `app:user` предназначены для локальной подготовки. Для production нужны HTTPS, `APP_ENV=production`, `APP_DEBUG=false`, корректный `APP_URL`, постоянный `APP_KEY`, настроенная почта, PostgreSQL с PostGIS и резервное копирование базы вместе с GIS-файлами. Корень web-сервера — `public/`; PHP должен иметь доступ на запись в `storage/` и `bootstrap/cache/`. Перед публикацией базы из локального окружения замените известные демо-пароли и проверьте права: production-флаг сам по себе эти аккаунты не удаляет.

Основные команды подготовки релиза после настройки окружения:

```bash
composer install --no-dev --prefer-dist --optimize-autoloader --no-interaction
npm ci
php artisan config:clear --no-interaction
php artisan migrate --force --no-interaction
php artisan db:seed --class=AccessControlSeeder --force --no-interaction
php artisan db:seed --class=SimulationDatasetSeeder --force --no-interaction
php artisan db:seed --class=GisDatasetSeeder --force --no-interaction
npm run build
php artisan config:cache --no-interaction
php artisan route:cache --no-interaction
php artisan view:cache --no-interaction
php artisan queue:restart --no-interaction
```

Запускайте эти шаги как часть релиза с резервной копией и согласованным переключением процессов. Создание первоначального production-администратора выполняется вашим процессом управления доступом; локальная команда `app:user` там недоступна.

Supervisor, systemd или менеджер процессов платформы должен поддерживать **два отдельных worker**:

```bash
php artisan queue:work --queue=agents,default --tries=1 --timeout=180 --no-interaction
php artisan queue:work --queue=gis --tries=4 --timeout=190 --memory=1024 --no-interaction
```

Настройте автоматический перезапуск после `queue:restart`, достаточное время для завершения текущей задачи и общий постоянный кэш для web и workers. Для расписания достаточно одного cron-вызова в минуту; замените `/path/to/hackalem` на каталог релиза:

```cron
* * * * * cd /path/to/hackalem && php artisan schedule:run --no-interaction >> /dev/null 2>&1
```

Для production SSR предусмотрены `npm run build:ssr` и отдельный управляемый процесс `php artisan inertia:start-ssr --no-interaction`; после смены сборки его также нужно перезапустить. `composer dev` не заменяет процессы production-сервера.

## Частые проблемы

| Симптом                                                       | Что проверить                                                                       |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Миграция сообщает, что PostGIS недоступен или не хватает прав | Установку PostGIS для нужной версии PostgreSQL и расширение в выбранной базе        |
| AI-задача остаётся в `queued`                                 | Worker очереди `agents`, соединение с БД, логи и scheduler                          |
| GIS-импорт не движется                                        | Отдельный worker `gis`, `gis:status`, свободное место и доступ к внешнему источнику |
| После изменения `.env` остался прежний режим                  | Кэш конфигурации и перезапуск процессов; старые задачи сохраняют снимок настроек    |
| Изменения интерфейса не видны или отсутствует Vite manifest   | Работающий `npm run dev` либо новая сборка `npm run build`                          |
| При входе нет доступа к карте или админпанели                 | Подтверждение email, роль и разрешения пользователя                                 |

## Инструменты разработки и устройство проекта

Пользовательские страницы находятся в `resources/js/pages`, симулятор — в `pages/scenarios` и `components/simulator`, GIS — в `app/Actions/Gis`, AI runtime — в `app/Ai`, жизненный цикл задач — в `app/Actions/AgentRuns` и `app/Jobs`. Filament использует собственный Livewire UI.

`AGENTS.md`, `CLAUDE.md`, `.agents/skills`, `.claude/skills`, `.codex/config.toml`, `.mcp.json` и `boost.json` содержат инструкции и настройки coding-агентов. Обновление и запуск Boost:

```bash
composer boost:refresh
php artisan boost:mcp
```

Вторая команда запускает STDIO-сервер для MCP-клиента из корня проекта. Boost — dev dependency с инструментами разработчика; его не следует подключать к пользовательскому AI runtime или публиковать как внешний сервис. `composer boost:refresh` меняет сгенерированные инструкции и настройки, поэтому проверяйте diff после запуска.

Подробности: [разработка](docs/development.md), [архитектура и ограничения](docs/architecture.md), [оценка и расширение](docs/evaluation.md). Коммиты, push и deployment выполняются только по явной команде пользователя.

## Источники

- [Laravel React starter kit](https://github.com/laravel/react-starter-kit), основа из snapshot `717b8f55aefd82d25d4119eaebdc8e3a72b8d7e5`.
- [Laravel AI SDK](https://laravel.com/docs/13.x/ai-sdk) и [Laravel Boost](https://laravel.com/docs/13.x/boost).
- [Очереди Laravel](https://laravel.com/docs/13.x/queues) и [планировщик](https://laravel.com/docs/13.x/scheduling).
- [Inertia 3: SSR](https://inertiajs.com/docs/v3/advanced/server-side-rendering) и [Filament 5](https://filamentphp.com/docs/5.x/introduction/installation).
