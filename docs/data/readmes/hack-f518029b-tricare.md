# EKT AI — Intelligent Shopping Assistant

AI-консультант для интернет-магазина электротехнической продукции **EKT / ГК Электрокомплект**, разработанный в рамках HackAlem AI.

EKT AI помогает пользователю искать товары естественным языком, работать с техническими характеристиками, проверять наличие по городам, находить аналоги и добавлять выбранные позиции в корзину.

---

## Problem

Каталог электротехнической продукции содержит большое количество технически сложных товаров.

Пользователь может:

- не знать точное название товара;
- знать только необходимые характеристики;
- искать товар по артикулу;
- хотеть проверить наличие в конкретном городе;
- искать замену отсутствующей позиции;
- не понимать различия между похожими товарами.

Обычный поиск по каталогу требует знания структуры сайта и характеристик продукции.

---

## Solution

**EKT AI** добавляет conversational AI-интерфейс поверх каталога EKT.

Пользователь может написать:

```text
Нужен трёхполюсный автомат Legrand 160А.
```

или:

```text
Есть ли этот товар в Алматы?
```

или:

```text
Если его нет, найди аналог.
```

Frontend передаёт запрос в **n8n workflow**, который обрабатывает пользовательский запрос, взаимодействует с AI и данными EKT и возвращает структурированный результат.

---

# Key Features

## AI Product Search

Поиск товаров по:

- названию;
- артикулу;
- бренду;
- техническим характеристикам;
- запросу на естественном языке.

AI может задавать уточняющие вопросы, если характеристик недостаточно.

---

## Product Information

Карточка товара поддерживает:

- название;
- артикул;
- цену;
- изображение;
- технические характеристики;
- общий остаток;
- остатки по складам;
- ссылку на товар.

Фактические данные товара должны поступать из EKT data/API, а не генерироваться AI.

---

## City-aware Availability

Пользователь выбирает город в интерфейсе.

Выбранный город отправляется в n8n вместе с запросом:

```json
{
  "city": "Алматы"
}
```

Поддерживаются:

```text
Алматы
Астана
Шымкент
Тараз
Атырау
Актау
Караганда
Талдыкорган
Усть-Каменогорск
```

Также учитываются различия в названиях складов, например:

```text
Астана ↔ Нур-Султан
```

---

## Explainable Analog Search

Если нужный товар отсутствует, EKT AI может предложить технически близкий аналог.

Пользователь получает не только рекомендацию, но и объяснение:

```text
✓ совпадающие характеристики
△ отличающиеся характеристики
```

Пример:

```text
✓ количество полюсов совпадает
✓ напряжение совпадает
✓ номинальный ток совпадает

△ отключающая способность отличается
```

---

## Russian / Kazakh

Интерфейс поддерживает:

```text
RU — русский
ҚАЗ — қазақша
```

Выбранный язык передаётся в n8n с каждым запросом.

```json
{
  "language": "kz"
}
```

Если выбран `kz`, объяснения AI должны возвращаться на казахском языке.

Названия брендов, моделей, артикулы и технические обозначения могут сохраняться в оригинальном виде.

---

## Shopping Cart

AI не добавляет товар автоматически.

Используется explicit confirmation:

```text
AI recommends product
        ↓
Product Card
        ↓
User clicks "В корзину"
        ↓
Confirmation Modal
        ↓
Quantity validation
        ↓
User confirms
        ↓
localStorage
        ↓
cart.html
```

Корзина поддерживает:

- изменение количества;
- ограничение количества доступным остатком;
- удаление товара;
- расчёт общей стоимости;
- сохранение состояния после обновления страницы.

---

# Architecture

```text
┌──────────────────────────┐
│          USER            │
│                          │
│ RU / ҚАЗ                 │
│ Selected city            │
│ Natural language query   │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│        FRONTEND          │
│                          │
│ HTML                     │
│ CSS                      │
│ Vanilla JavaScript       │
└─────────────┬────────────┘
              │
              │ POST
              ▼
┌──────────────────────────┐
│       n8n WEBHOOK        │
│                          │
│ /webhook/assistant       │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│    n8n ORCHESTRATION     │
│                          │
│ Request processing       │
│ AI integration           │
│ EKT data/API             │
│ Response normalization   │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│   STRUCTURED RESPONSE    │
│                          │
│ text                     │
│ product                  │
│ analog                   │
│ purchase_info            │
│ error                    │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│        FRONTEND          │
│                          │
│ AI message               │
│ Product Card             │
│ Analog Card              │
│ Cart confirmation        │
└──────────────────────────┘
```

Подробное описание:

```text
docs/architecture.md
```

---

# Tech Stack

## Frontend

- HTML5
- CSS3
- Vanilla JavaScript
- Browser localStorage

## AI / Orchestration

- n8n
- AI / LLM API
- EKT product data/API

## AI Infrastructure

В рамках проекта предусмотрено использование доступных API credits:

- OpenAI API
- NVIDIA API

Конкретные модели определяются конфигурацией финального n8n workflow.

API keys не хранятся во frontend.

---

# Project Structure

После объединения frontend и n8n веток структура проекта:

```text
EKT_AI/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── cart.html
│   └── cart.js
│
├── n8n/
│   └── ...
│
├── data/
│   ├── sample_products.json
│   └── sample_product_detail.json
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── demo-scenarios.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

# Running the Project

## 1. Clone Repository

```bash
git clone https://github.com/BAITC-Hacks/hack-f518029b-tricare.git
```

Перейдите в проект:

```bash
cd hack-f518029b-tricare
```

---

## 2. Run Frontend

Перейдите в папку:

```bash
cd frontend
```

Запустите локальный HTTP server:

```bash
python -m http.server 5500
```

Откройте:

```text
http://localhost:5500/index.html
```

> Не рекомендуется запускать страницу через `file://`, поскольку browser origin и localStorage будут отличаться от HTTP-запуска.

---

## 3. Configure n8n

Импортируйте workflow из папки:

```text
n8n/
```

Настройте необходимые credentials в n8n.

В зависимости от финальной конфигурации workflow могут использоваться:

```text
OpenAI API
NVIDIA API
EKT API
```

После настройки активируйте workflow.

---

## 4. n8n Webhook

Frontend взаимодействует с Production Webhook:

```text
POST /webhook/assistant
```

Пример запроса:

```json
{
  "session_id": "ekt-...",
  "message": "Нужен автомат Legrand 160А",
  "language": "ru",
  "city": "Алматы"
}
```

---

# API Response Contract

n8n должен возвращать структурированный JSON.

## Text

```json
{
  "type": "text",
  "message": "Уточните количество полюсов."
}
```

## Product

```json
{
  "type": "product",
  "message": "Нашёл подходящий товар.",
  "product": {
    "id": 515291,
    "name": "027228 АВ DRX250 MT 3ф 160А 18kA Legrand",
    "article": "200300285_",
    "price": 64920,
    "quantity": 23,
    "image": "https://...",
    "url": "https://...",
    "stores": [],
    "properties": {}
  }
}
```

## Analog

```json
{
  "type": "analog",
  "message": "Нашёл технически близкий аналог.",
  "product": {},
  "match": {
    "score": 92,
    "reasons": [],
    "differences": []
  }
}
```

Полный контракт:

```text
docs/api-contract.md
```

---

# EKT Data

В папке `data/` находятся примеры структуры данных EKT:

```text
sample_products.json
sample_product_detail.json
```

Они используются для:

- разработки;
- тестирования;
- демонстрации структуры каталога;
- воспроизводимости проекта.

Sample JSON не должен рассматриваться как источник актуальной цены или остатка.

Актуальные данные должны поступать из EKT API/workflow.

---

# Demo Scenarios

## Product Search

```text
Нужен трёхполюсный автомат Legrand 160А.
```

Ожидается поиск релевантной позиции в каталоге.

## Stock

Выбрать:

```text
Алматы
```

и спросить:

```text
Есть ли этот товар в наличии?
```

## Analog

```text
Если его нет, найди аналог.
```

Система должна показать технически близкую позицию и объяснить отличия.

## Kazakh

Переключить:

```text
ҚАЗ
```

и написать:

```text
Маған үш полюсті автоматты ажыратқыш керек.
```

Ответ AI должен быть на казахском языке.

## Cart

```text
Product Card
      ↓
В корзину
      ↓
Confirmation
      ↓
Quantity
      ↓
Да, добавить
      ↓
cart.html
```

Подробнее:

```text
docs/demo-scenarios.md
```

---

# AI Grounding

AI используется для:

- понимания естественного языка;
- определения пользовательского intent;
- извлечения характеристик;
- объяснения результатов;
- объяснения аналогов;
- формирования понятного ответа.

AI не должен самостоятельно придумывать:

```text
price
stock
article
product id
technical properties
product URL
```

Эти данные должны поступать из EKT.

---

# Security

Нельзя хранить во frontend или публиковать в GitHub:

```text
OPENAI_API_KEY
NVIDIA_API_KEY
EKT private credentials
```

Секретные данные должны находиться в:

- n8n Credentials;
- environment variables;
- локальном `.env`.

`.env` должен находиться в `.gitignore`.

Пример переменных без секретных значений хранится в:

```text
.env.example
```

---

# Current Prototype Scope

Hackathon prototype демонстрирует:

- AI-assisted product search;
- работу с EKT product data;
- RU / ҚАЗ;
- проверку наличия;
- подбор аналогов;
- объяснимые рекомендации;
- explicit cart confirmation;
- локальную корзину;
- n8n orchestration.

Прототип не выполняет:

- реальную оплату;
- production checkout;
- изменение production-корзины EKT;
- хранение платёжных данных.

---

# Documentation

```text
docs/architecture.md
docs/api-contract.md
docs/demo-scenarios.md
```

---

# Team Workflow

Разработка выполнялась параллельно:

```text
main
→ frontend
→ cart
→ documentation

aibarys
→ n8n workflow
→ AI / EKT integration
```

Перед финальной сдачей изменения объединяются в `main`.

---

# Final Demo Checklist

- [ ] Frontend запускается через HTTP.
- [ ] n8n workflow активен.
- [ ] Frontend → n8n возвращает HTTP 200.
- [ ] n8n возвращает структурированный JSON.
- [ ] Поиск товара работает.
- [ ] Цена и остаток поступают из EKT data.
- [ ] RU работает.
- [ ] ҚАЗ работает.
- [ ] Выбор города работает.
- [ ] Аналог содержит объяснение.
- [ ] Добавление в корзину требует подтверждения.
- [ ] Количество ограничено остатком.
- [ ] `cart.html` работает.
- [ ] Корзина сохраняется после F5.
- [ ] `.env` отсутствует в GitHub.
- [ ] Финальный n8n workflow присутствует в репозитории.

---

## EKT AI

**AI-powered product discovery for electrical equipment.**

Search. Understand. Compare. Choose.
