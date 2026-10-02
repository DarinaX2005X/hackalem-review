# Memory Munchers

Репозиторий команды Memory Munchers для хакатона.

Приложение — каталог товаров с AI-помощником и корзиной:

- **Бэкенд** — ASP.NET Core (.NET 10) в `MemoryMunchers/MemoryMunchers`, база данных PostgreSQL, AI-агент через OpenAI Responses API.
- **Фронтенд** — статические HTML/JS-страницы без зависимостей в папке `frontend`.

## Локальный запуск

### 1. Установите необходимые программы

- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0) — проверьте командой `dotnet --version`.
- [PostgreSQL](https://www.postgresql.org/download/) (версия 14 или новее).
- [Python 3](https://www.python.org/downloads/) — только для раздачи статических файлов фронтенда (можно использовать любой другой статический сервер).

### 2. Установите и настройте PostgreSQL

**Windows:**

1. Скачайте установщик с [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) и запустите его.
2. Оставьте порт по умолчанию `5432`.
3. Задайте пароль для пользователя `postgres` — он понадобится для строки подключения.
4. Дождитесь окончания установки (Stack Builder можно пропустить).

**Или через Docker:**

```powershell
docker run --name memory-munchers-db -e POSTGRES_PASSWORD=123 -p 5432:5432 -d postgres:17
```

Создавать базу данных вручную не нужно: при запуске API сам создаст базу `memory_munchers` и применит миграции. Пользователю БД нужны права на установку расширения `pg_trgm` (у пользователя `postgres` они есть).

### 3. Подключите приложение к PostgreSQL

Откройте `MemoryMunchers/MemoryMunchers/appsettings.json` и укажите свои данные в строке подключения:

```json
"ConnectionStrings": {
  "MemoryMunchers": "Host=localhost;Port=5432;Database=memory_munchers;Username=postgres;Password=ВАШ_ПАРОЛЬ"
}
```

Измените `Password` (и при необходимости `Host`, `Port`, `Username`) на значения, заданные при установке PostgreSQL.

Вместо правки файла можно задать переменную окружения:

```powershell
$env:ConnectionStrings__MemoryMunchers = "Host=localhost;Port=5432;Database=memory_munchers;Username=postgres;Password=ВАШ_ПАРОЛЬ"
```

### 4. Добавьте API-ключ OpenAI

Ключ нужен для работы AI-помощника (каталог и корзина работают и без него).

1. Создайте ключ на [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Сохраните его в user-secrets. Это хранилище вне репозитория, и API подхватывает его в режиме Development:

```powershell
dotnet user-secrets set "OpenAI:ApiKey" "sk-ваш-ключ" --project MemoryMunchers/MemoryMunchers
```

Либо задайте переменную окружения (она имеет приоритет над `appsettings.json`):

```powershell
$env:OpenAI__ApiKey = "sk-ваш-ключ"
```

> ⚠️ Не вписывайте ключ в `appsettings.json`: этот файл коммитится. Во фронтенд ключ тоже не добавляйте.

Если ключ не задан, запросы к агенту вернут HTTP 503 с кодом `provider_not_configured`.

### 5. Запустите API

Из корня репозитория:

```powershell
dotnet run --project MemoryMunchers/MemoryMunchers --launch-profile http
```

API будет доступен по адресу `http://localhost:5187`. При старте автоматически применяются миграции базы данных.

### 6. Запустите фронтенд

В другом терминале, из корня репозитория:

```powershell
python -m http.server 5500 --directory frontend
```

### 7. Откройте приложение

Откройте в браузере `http://localhost:5500`.

При старте API сам импортирует каталог из `MemoryMunchers/MemoryMunchers/nursultan_ekt_catalog.csv` (около 12 853 товаров), а затем демо-фиды остатков и сертификатов (см. ниже). Первый запуск может занять некоторое время.

Страницы:

| Адрес | Что открывается |
| --- | --- |
| `http://localhost:5500/` | Каталог товаров с чатом **Помощник** |
| `http://localhost:5500/basket.html` | Корзина |

Фронтенд по умолчанию обращается к API по адресу `http://localhost:5187`. Изменить адрес можно в блоке **Подключение к серверу** на странице. Если фронтенд открыт с другого адреса (не `localhost:5500`), добавьте этот адрес в `Cors:AllowedOrigins`, иначе браузер заблокирует запросы.

## Что умеет помощник

| Требование | Как реализовано |
| --- | --- |
| Наличие, характеристики, сертификаты | `get_product_details` возвращает остаток (`availableQuantity`, `stockStatus`), характеристики и сертификаты со ссылкой `/api/certificates/{id}` |
| Аналоги при отсутствии товара | `find_product_alternatives` исключает товары с нулевым остатком и ранжирует кандидатов по типу товара (словам из названия), совпадающим характеристикам, подкатегории, бренду, наличию и цене. Для каждого аналога возвращается текстовое обоснование `reason`, которое показывается в карточке. |
| Условия покупки | `get_purchase_conditions`: оплата, доставка, самовывоз, возврат и минимальный заказ из `Shopping:PurchaseConditions` (взяты с nursultan.ekt.kz), плюс минимум и кратность по конкретным товарам |
| Корзина только после подтверждения | Агент создаёт только *предложение*. Корзина меняется лишь по нажатию «Подтвердить добавление». Количество проверяется по остатку, минимуму, кратности и лимиту; если цена или остаток изменились, подтверждение отклоняется. |
| Ссылка на корзину | После подтверждения в чате появляется ссылка `Shopping:BasketUrl`; со страницы корзины можно перейти к оформлению (`Shopping:CheckoutUrl`) |

## Безопасность и приватность

- **Изоляция покупателей.** Каждый браузер получает анонимный подписанный токен (`POST /api/shopper`, ASP.NET Data Protection). Токен передаётся в заголовке `X-Shopper-Token`. Корзина, диалоги и файлы видны только владельцу токена; без токена API отвечает 401.
- **Защита корзины от посторонних изменений.** Cookie не используются, поэтому сторонний сайт не может отправить запрос от имени покупателя (CSRF). CORS разрешён только для адресов из `Cors:AllowedOrigins`. Подтвердить чужое предложение нельзя: API ответит 404.
- **Ограничение частоты запросов** (`RateLimits`): сообщения в чат, загрузка файлов, операции с корзиной и выдача токенов. При превышении API отвечает 429.
- **Хранение данных.** Вложения удаляются через `AttachmentLifetimeHours`, диалоги — после `SessionRetentionDays` дней неактивности. Кнопка «Удалить мои данные» в чате (`DELETE /api/shopper`) сразу удаляет диалоги, файлы и корзину. OpenAI вызывается с `store: false`, тексты сообщений в логи не пишутся. Агенту запрещено запрашивать персональные данные.

## Данные магазина: остатки и сертификаты

Публичный каталог не содержит остатков и сертификатов, поэтому их загружают отдельными фидами (например, выгрузкой из 1С). Формат — CSV с разделителем `;`:

| Фид | Колонки |
| --- | --- |
| Остатки | `ID товара;Остаток[;Проверено UTC]` |
| Сертификаты | `ID товара;Номер;Тип;Выдан;Действует до;URL;Файл` (файлы кладутся в папку `certificates/` рядом с API) |

Загрузка реальных фидов (задайте `Admin:ApiKey`, по умолчанию эндпоинты выключены):

```powershell
curl.exe -X POST -H "X-Admin-Key: <ключ>" -F "file=@inventory.csv" http://localhost:5187/api/admin/inventory
curl.exe -X POST -H "X-Admin-Key: <ключ>" -F "file=@certificates.csv" http://localhost:5187/api/admin/certificates
```

**Демо-данные.** При `DemoData:Enabled = true` API загружает `demo_inventory.csv` и `demo_certificates.csv` при старте, а остатки обновляет каждые 6 часов. Остатки сгенерированы: у позиций «Купить» от 5 до 184 шт., у каждой 9-й — 0. Позиции «Под заказ» без остатка. Сертификаты (у каждого 10-го товара) помечены «ДЕМО» и не являются реальными документами. Остатки старше `InventoryMaxAgeMinutes` считаются неизвестными. Для продакшена выключите `DemoData:Enabled` и загружайте реальные фиды.

## Встраивание в сайт (1С-Битрикс)

Сайт nursultan.ekt.kz работает на 1С-Битрикс. Чат встраивается без изменений в движке: подключите в шаблоне (например, в `footer.php`) стили и скрипты, опубликованные вместе с API:

```html
<link rel="stylesheet" href="https://assistant.example/chatbot.css">
<script src="https://assistant.example/shopping.js" data-api="https://api.assistant.example" data-basket-url="https://assistant.example/basket.html" defer></script>
<script src="https://assistant.example/chatbot.js" defer></script>
```

Затем добавьте адрес сайта в `Cors:AllowedOrigins` и пропишите `Shopping:BasketUrl`, `Shopping:PublicApiUrl` и `Shopping:CheckoutUrl` (сейчас это `https://nursultan.ekt.kz/personal/cart/`). Вёрстка адаптивная: на экранах до 520 px чат открывается на весь экран.

> Автоматический перенос позиций в корзину Битрикс (`sale.basketitem.add` через REST) требует доступа к API сайта и пока не подключён. До этого кнопка «Оформить заказ на сайте» открывает корзину сайта, а товары открываются по ссылкам из карточек.

## Тесты

Приёмочные тесты по каждому пункту Must have, а также по изоляции покупателей, CORS и удалению данных лежат в `MemoryMunchers/MemoryMunchers.Tests`. Они запускают настоящий API на отдельной базе `memory_munchers_tests`; OpenAI при этом не вызывается, инструменты агента выполняются напрямую.

```powershell
dotnet test MemoryMunchers/MemoryMunchers.Tests
```

Другую базу можно задать через `$env:MM_TEST_CONNECTION = "Host=...;Database=...;Username=...;Password=..."`.

## Частые проблемы

- **Ошибка подключения к базе** — проверьте, что PostgreSQL запущен, и что пароль/порт в строке подключения верные.
- **Ошибка при установке `pg_trgm`** — используйте пользователя с правами суперпользователя или попросите администратора выполнить `CREATE EXTENSION pg_trgm;` в базе `memory_munchers`.
- **Помощник не отвечает (HTTP 503)** — не задан `OpenAI:ApiKey`. Добавьте ключ и перезапустите API.
- **HTTP 401 `shopper_required`** — токен покупателя устарел (например, после смены ключей Data Protection). Обновите страницу: фронтенд получит новый токен сам.
- **Запросы блокируются CORS** — добавьте адрес, с которого открыт фронтенд, в `Cors:AllowedOrigins`.
- **HTTP 500** — смотрите логи API в терминале, где он запущен.

## Ручное применение миграций (необязательно)

Миграции применяются при старте API, но их можно применить и вручную из корня репозитория:

```powershell
dotnet tool restore
dotnet ef database update --project MemoryMunchers/MemoryMunchers
```

На сайте, агента можно найти тут:
<img width="1787" height="875" alt="Агент" src="https://github.com/user-attachments/assets/1a0146ad-eae3-46e9-92fd-26a3545d4eee" />

## Есть еще алтернативная версия решения на python в ветке `alternative_version`.
