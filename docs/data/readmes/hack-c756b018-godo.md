<img width="1376" height="768" alt="image" src="https://github.com/user-attachments/assets/1c25db11-d6cf-4112-905c-19d642c10907" />

# Career Quest

AI-навигатор карьерного развития сотрудников (кейс Halyk Bank). Сотрудник видит, чего не хватает до следующего грейда, и получает 1–3 активности с объяснением «почему именно это». HR видит, где команда проседает, и кому стоит обсудить развитие.

## Зачем и как это работает

Проблема: каталог обучения большой, сотрудник не понимает, что двигает его к следующему грейду, а часть мероприятий системно пропускает. Career Quest берёт три набора данных — профиль навыков, требования грейдов и историю участия — и превращает их в короткий персональный план.

Конвейер рекомендации (`backend/src/modules/recommendations/recommendations.service.ts`):

1. **Карта цели.** Из `skills.json` берётся матрица `requirementsByGrade` для роли и целевого грейда сотрудника — что и на каком уровне нужно.
2. **Жёсткие префильтры.** Навык с 2+ пропусками или отказами (MISSED/REFUSED) исключается целиком — повторное предложение того, что сотрудник уже отверг, бесполезно. Далее отбрасываются пройденные события, события по навыку на `maxLevel` и не подходящие по аудитории.
3. **Разрыв (skill gap).** Для каждого оставшегося события: `требуемый уровень − текущий` и прогноз прироста `min(gain, maxLevel − current)`.
4. **TOP-5 → LLM.** В OpenAI (`gpt-4o-mini`, JSON-режим) уходит только компактный контекст: один сотрудник и 5 кандидатов. Модель выбирает ID строго из этого списка и пишет короткое объяснение.
5. **Guardrails.** Ответ модели проверяется: несуществующий `eventId`, сломанная структура или таймаут 8 с — ответ собирается локальным алгоритмическим рейтингом. Без `OPENAI_API_KEY` API работает так же, только сразу по локальному порядку. Демо не падает никогда.
6. **Объяснение на фактах.** В каждом ответе есть проверяемые числа — грейды, текущий и требуемый уровень, разрыв, прогноз прироста, история по навыку. Текст модели добавляется к фактам, а не заменяет их.

Отметка «пройдено» атомарно повышает навык до `min(current + gain, maxLevel)`, пишет `COMPLETED` в историю и пересчитывает готовность к целевому грейду.

## Что использовано и где

| Технология | Где | Зачем |
| --- | --- | --- |
| NestJS 11 + TypeScript | `backend/src` | REST API: модули `employee`, `hr`, `recommendations`, `data-importer`; Swagger на `/docs` |
| TypeORM 0.3 + PostgreSQL 15 | `backend/src/storage` | 4 таблицы; навыки сотрудника и требования грейдов — JSONB; схема синхронизируется автоматически (`synchronize: true`) |
| class-validator / class-transformer | DTO модулей | Валидация входных данных, `whitelist` против лишних полей |
| OpenAI Chat Completions (`gpt-4o-mini`) | `recommendations.service.ts` | Выбор 1–3 мероприятий из отфильтрованного списка и объяснение; JSON-режим, таймаут, алгоритмический fallback |
| Next.js 16 + React 19 | `frontend/app` | Страницы `/` (выбор роли), `/employee`, `/hr`, `/hr/employees/[id]`; запросы к backend по `/api/*` (`BACKEND_URL`) |
| Tailwind CSS 4 + lucide-react | `frontend` | Стиль интерфейса и иконки |
| Framer Motion, Zustand | `frontend` | Анимация прогресс-баров, клиентское состояние профиля |
| Docker Compose | `backend/docker-compose.yml` | Три сервиса: `db`, `backend`, `frontend`; `backend/data` монтируется в контейнер для импорта данных жюри |
| Jest | `backend/src/**/*.spec.ts` | Юнит-тесты префильтра рекомендаций, импортёра датасета и ролевого guard |


2. Backend — каталог backend/
cd backend
npm install
copy .env.example .env    # впишите OPENAI_API_KEY (необязательно, иначе локальный рейтинг)
npm run start:dev         # watch-режим
→ API: http://localhost:3000, Swagger: http://localhost:3000/docs. При первом старте в пустую БД сам импортирует демоданные из backend/data/.

3. Frontend — каталог frontend/ (вторая вкладка терминала)
cd frontend
npm install
npm run dev
→ http://localhost:3001. Все запросы идут на свой же /api/* и проксируются на backend; если backend на другом адресе — BACKEND_URL=http://localhost:3000 npm run dev.
## Демо-доступ

Для хакатона — заголовки вместо SSO (осознанное ограничение демо): `X-Role: employee | hr` и `X-Employee-Id` для сотрудника. `RolesGuard` подключён глобально (`APP_GUARD`) и возвращает `403`, если сотрудник лезет в HR-разделы или в чужой профиль. Переключатель роли встроен в интерфейс.

Демоданные из `backend/data/` (`employees.json`, `events.json`, `skills.json`, `activity_history.csv`) импортируются автоматически при первом старте в пустую БД. Полная замена — `POST /api/admin/import`; дозагрузка отдельных записей — `POST /api/hr/import` или HR-экран (JSON и CSV разбираются на клиенте). `skipped` в CSV становится `MISSED`; история с неизвестным сотрудником или событием откатывает транзакцию импорта.

## API

Интерактивная документация: `http://localhost:3000/docs`. Основные маршруты (префикс `/api` опционален):

| Метод | Путь | Роль | Описание |
| --- | --- | --- | --- |
| GET | `/employees/:id` | emp / hr | Профиль: навыки с уровнями, требованиями и готовностью |
| GET | `/employees/:id/recommendations` | emp / hr | 1–3 рекомендации с обоснованием и breakdown по фактам |
| POST | `/employees/:id/complete-event/:eventId` | emp | Отметить пройденным, вернуть обновлённый профиль |
| POST | `/activities/complete` | emp | То же по `employeeId` + `eventId` в теле |
| GET | `/hr/employees` | hr | Список сотрудников с готовностью и статусом |
| GET | `/hr/analytics` | hr | Топ-5 проседающих навыков, сотрудники без шага, участие по событиям |
| GET | `/hr/employees/:id` | hr | Профиль сотрудника, только просмотр |
| POST | `/hr/import` | hr | Дозагрузка JSON-датасета (merge) |
| POST | `/api/admin/import` | hr | Полная замена данных из файлов `backend/data` |

Примеры:

```sh
# Профиль и рекомендации сотрудника
curl http://localhost:3000/employees/E0028 -H "X-Role: employee" -H "X-Employee-Id: E0028"
curl http://localhost:3000/employees/E0028/recommendations -H "X-Employee-Id: E0028"

# HR-аналитика
curl http://localhost:3000/hr/analytics -H "X-Role: hr"
```

Frontend — http://localhost:3001, backend — http://localhost:3000, Swagger — http://localhost:3000/docs.

Локально без Docker: поднять Postgres (`docker compose up db`), затем `npm install && npm run start:dev` в `backend/` и `npm install && npm run dev` в `frontend/`.

Переменные backend: `DB_URL` (или `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`), `AI_PROVIDER=openai`, `OPENAI_API_KEY`, опционально `OPENAI_MODEL` (по умолчанию `gpt-4o-mini`) и `OPENAI_MAX_TOKENS`.

## Проверка

```sh
cd backend  && npm run build && npm test -- --runInBand
cd frontend && npm run typecheck
```

Ручной сценарий: откройте сотрудника `E0028` — Public Speaking (3 пропуска в истории) не должен попасть в рекомендации, а System Design с разрывом 2 до Senior — должен. Отметьте активность пройденной: уровень навыка вырастет, готовность пересчитается. Запрос `/hr/analytics` с ролью `employee` возвращает `403`.

## Ограничения демо

Роль передаётся заголовком и подделывается вручную — для банка нужен SSO/JWT и серверная проверка личности; схема БД синхронизируется автоматически вместо миграций. Эти места помечены в коде и меняются без перестройки остальной логики.
