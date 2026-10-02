# EKT.kz — ИИ-консультант по электротехнике

Веб-приложение для подбора электротехнического оборудования EKT.kz. Проект помогает электрикам, проектировщикам, монтажникам, снабженцам и частным клиентам искать товары, проверять наличие, выполнять базовые расчёты нагрузки и получать рекомендации ИИ-консультанта.

## Что реализовано

- каталог товаров с поиском, фильтрами, сортировкой и пагинацией;
- выбор города и склада: Астана, Алматы, Шымкент, Караганда и другие города Казахстана;
- карточки товаров с ценой, характеристиками, изображениями и остатками;
- корзина с добавлением товаров, изменением количества и удалением позиций;
- инженерный калькулятор для сетей 220 В и 380 В: ток, номинал автомата и ориентировочное сечение кабеля;
- чат «ИИ-инженер EKT» с подбором товаров по запросу;
- голосовой ввод и озвучивание ответа в браузере;
- подбор возможных аналогов товара по категории и характеристикам;
- локальный rule-based fallback, если Gemini недоступен;
- Android-приложение на Jetpack Compose с отдельным Gemini-консультантом.

## Как работает

Пользователь вводит запрос, параметры фильтра или данные нагрузки. Frontend отправляет запрос в локальный FastAPI backend. Backend получает каталог и остатки через EKT API. Для консультации сообщение передаётся Express-серверу: он обращается к Google Gemini, извлекает рекомендованные товары и показывает их в интерфейсе. При отсутствии ключа Gemini используется локальный набор инженерных правил. Результат можно применить к каталогу и добавить товар в корзину.

## Технологии

- **Frontend:** TypeScript, React 19, Vite, Express, Tailwind CSS, `lucide-react`, `motion`.
- **Backend:** Python, FastAPI, Uvicorn, Pydantic, HTTPX.
- **AI:** Google Gemini через `@google/genai`; в Express-коде указана модель `gemini-3.8-flash`, в Android-клиенте — `gemini-3.5-flash`.
- **Android:** Kotlin, Jetpack Compose, Material 3, Room, Retrofit, OkHttp, Moshi, Coil, Coroutines.
- **Браузерные API:** Web Speech API и Speech Synthesis API.

## Архитектура

```text
React/Vite + Express (frontend:3000)
  ├─ /api/chat → Gemini или локальный fallback
  └─ src/services/api.ts → FastAPI (backend:8000)
			      ├─ каталог и детали товаров
			      ├─ корзина
			      └─ аналоги товаров
				      ↓
			      EKT API: https://ekt.kz/api

Android Compose-приложение → локальные данные/Room → Gemini API
```

Основные компоненты: `frontend/src` содержит интерфейс и клиент API; `frontend/server.ts` обслуживает React и чат; `backend/main.py` содержит HTTP-маршруты; `backend/ekt_client.py` работает с EKT API; `backend/analog_service.py` подбирает аналоги; `backend/cart_store.py` хранит корзины в памяти.

## Установка и запуск

### Backend

В PowerShell из корня проекта:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

При необходимости заполните `backend\.env`:

```dotenv
EKT_API_URL=https://ekt.kz/api
EKT_API_USERNAME=
EKT_API_PASSWORD=
```

### Frontend

Во втором терминале:

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Для ИИ укажите в `frontend\.env`:

```dotenv
GEMINI_API_KEY=ваш_ключ_Gemini
```

Откройте [http://localhost:3000](http://localhost:3000). Проверка сборки и типов:

```powershell
npm run build
npm run lint
```

### Android

Откройте каталог `app/apps` в Android Studio, создайте `.env` на основе `app/apps/.env.example`, дождитесь синхронизации Gradle и запустите модуль `app` на эмуляторе или устройстве. Для release-сборки нужны `KEYSTORE_PATH`, `STORE_PASSWORD` и `KEY_PASSWORD`.

## Как проверить

1. Запустите backend и frontend.
2. В каталоге найдите `Legrand`, откройте карточку товара и добавьте его в корзину.
3. Откройте калькулятор, выберите `3 фазы (380 В)`, укажите `30 кВт` и `cos φ = 0.85`; примените рассчитанный номинал к каталогу.
4. В чате отправьте: `Реле контроля сухого хода насоса`.
5. Проверьте ответ консультанта и рекомендованные товары.
6. Проверьте API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) должен вернуть `{"status":"ok"}`. Документация доступна по [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Данные и интеграции

- живой каталог и остатки: `https://ekt.kz/api`;
- авторизация EKT API: `EKT_API_USERNAME` и `EKT_API_PASSWORD` через HTTP Basic Auth;
- frontend обращается к FastAPI по `http://127.0.0.1:8000`;
- Express предоставляет `/api/chat`, локальные маршруты каталога и городов;
- Gemini используется для генерации консультаций, а демонстрационные товары из `frontend/src/data/mockProducts.ts` входят в базу знаний frontend-консультанта;
- корзина frontend сохраняется в `localStorage`, backend-корзина хранится в памяти процесса.

## Ограничения

- Подтверждённой production/deployed-ссылки web-версии в репозитории нет; для демонстрации используется локальный адрес `http://localhost:3000`.
- Для живого каталога может потребоваться действующая авторизация EKT API.
- Оформление заказа, оплата и интеграция с личным кабинетом EKT не реализованы.
- Backend-корзина хранится только в RAM и очищается после перезапуска сервера.
- Поиск и подбор аналогов ограничены просмотренными страницами каталога; аналоги требуют технической проверки перед заменой.
- Расчёты являются ориентировочными и не заменяют полноценное проектирование электроснабжения.
- Адрес backend зафиксирован на `127.0.0.1:8000`; для публикации потребуется настроить reverse proxy, CORS и production-конфигурацию.

## Deployed-версия

В текущем репозитории подтверждённая deployed-версия web-приложения не указана.
