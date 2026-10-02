# Beeline Campaign Intelligence

Агентская система для задачи Beeline Tariff Marketing Campaigns. Система
выбирает план маркетинговых кампаний: клиентский сегмент, целевой тариф и
канал коммуникации. План содержит **не более 10 кампаний** и учитывает
пилотные эксперименты, эффект, стоимость контактов, бюджет и лимит контактов.

## Что решает система

Исторические данные относятся к другой выборке клиентов, поэтому эффект
кампании нельзя просто перенести из истории. Система сначала формирует
гипотезы по сегментам, проверяет лучшие гипотезы пилотами через
`env.run_pilot(...)`, затем выбирает прибыльные и непересекающиеся кампании.

В каждой кампании задаются:

- `filter_arpu_segment`: `LOW`, `MID` или `HIGH`;
- `filter_data_segment`: `NON_USER`, `LITE` или `HEAVY`;
- `filter_call_segment`: `LOW`, `MEDIUM` или `HIGH`;
- `filter_current_tariff`: текущий тариф;
- `target_tariff`: один из `tariff_1` ... `tariff_21`;
- `channel`: `push`, `sms`, `digital_ads` или `call`.

Агент не добавляет кампанию только ради достижения числа 10: если вариант
убыточен или повторно охватывает уже выбранную аудиторию, он отбрасывается.

## Архитектура

```text
CSV / SQLite / official environment
              |
              v
        Agent.act(env)
              |
       candidate campaigns
              |
       adaptive pilot tests
              |
      score + cost + constraints
              |
              v
       submission.csv + dashboard
```

Основные компоненты:

- [agent.py](./agent.py) — стратегия сегментации, пилотов, scoring и выбора
  кампаний;
- [db.py](./db.py) — создание воспроизводимой SQLite-базы для локальной
  демонстрации;
- [local_eval.py](./local_eval.py) — локальное окружение и проверка результата;
- [server.py](./server.py) — FastAPI backend;
- [frontend/](./frontend/) — dashboard без отдельного frontend-сборщика;
- [make_submission.py](./make_submission.py) — CLI-генератор `submission.csv`.

## Быстрый запуск с GitHub

```powershell
git clone https://github.com/BAITC-Hacks/hack-8692987e-404not-found.git
cd hack-8692987e-404not-found
py -3 -m pip install -r requirements.txt
```

### Запуск dashboard

```powershell
py -3 -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Откройте в браузере:

```text
http://127.0.0.1:8000
```

В dashboard можно:

1. посмотреть размер локальной базы и параметры каналов;
2. загрузить пользовательский CSV;
3. нажать «Запустить агента»;
4. увидеть выбранные кампании, score, бюджет, контакты и пилоты;
5. скачать или открыть созданный `submission.csv`.

### CLI-запуск без интерфейса

```powershell
py -3 make_submission.py
```

Команда создаёт `submission.csv` и печатает локальную оценку:

```text
Generated ... campaigns into submission.csv
Local evaluation: score=..., contacts=..., budget=..., within_limits=True
```

## Локальная база данных

Если запускается локальная версия, `db.py` автоматически создаёт файл
`campaigns.db`. База воспроизводимо содержит:

| Таблица | Содержание |
|---|---|
| `customer_profile` | 23 441 профиль клиентов |
| `tariff_dictionary` | 21 тариф |
| `traffic` | потребление минут, SMS и данных |
| `arpu_monthly` | месячный ARPU |
| `change_tariff` | 14 824 смены тарифов |
| `feature_dictionary` | описание признаков |

`campaigns.db` не хранится в Git: она генерируется из исходного кода при
первом запуске.

## Загрузка пользовательского CSV

В dashboard нажмите **«Выбрать CSV»**, затем после успешной загрузки нажмите
**«Запустить агента»**. Загруженный профиль реально используется следующим
запуском агента.

Обязательные колонки:

```csv
customer_id,current_tariff,arpu_segment,data_segment,call_segment,predicted_arpu
101,tariff_3,HIGH,HEAVY,HIGH,9000
102,tariff_7,MID,LITE,MEDIUM,3200
103,tariff_1,LOW,NON_USER,LOW,600
```

`customer_id` рекомендуется для контроля пересечения аудиторий. Значения
сегментов должны соответствовать указанным выше значениям.

## API

После запуска dashboard доступны:

| Метод | URL | Назначение |
|---|---|---|
| `GET` | `/api/status` | состояние сервиса и источник данных |
| `GET` | `/api/dataset` | таблицы базы, тарифы и каналы |
| `POST` | `/api/profile` | загрузка CSV профиля |
| `POST` | `/api/run` | запуск агента и локальной оценки |
| `GET` | `/api/submission` | текущий результат CSV в JSON |

Пример запуска через PowerShell:

```powershell
curl.exe -X POST -F "file=@my_profile.csv" http://127.0.0.1:8000/api/profile
curl.exe -X POST http://127.0.0.1:8000/api/run
```

## Ограничения и каналы

Система проверяет:

- максимум 10 кампаний;
- бюджет;
- суммарное количество контактов;
- допустимые тарифы и каналы;
- отсутствие повторного охвата одной аудитории;
- отсутствие убыточных кандидатов в финальном плане.

Локальная модель каналов:

| Канал | Стоимость контакта | Коэффициент эффективности |
|---|---:|---:|
| `push` | 0 | 0.50 |
| `sms` | 4 | 0.65 |
| `digital_ads` | 22 | 0.85 |
| `call` | 160 | 1.20 |

Пилоты используют разные размеры выборки. Большая выборка получает больший
вес доверия, поэтому один неудачный маленький пилот не должен полностью
сломать решение.

## Подключение официального judge

Локальный `local_eval.py` предназначен для воспроизводимой демонстрации и
smoke-тестирования. Официальный judge и оригинальный пакет данных должны
заменить локальную модель оценки перед конкурсным запуском.

### Вариант A: официальный модуль окружения

Если организаторы дают `local_eval.py`, `eval.py`, `runner.py` или `main.py`,
положите файл в корень проекта и убедитесь, что в нём есть один из интерфейсов:

```python
def make_env():
    ...
```

или:

```python
env = ...
```

`make_submission.py` пытается найти такое окружение автоматически и передать
его в `Agent.act(env)`.

### Вариант B: официальные CSV-данные

Положите данные в отдельную папку, например:

```text
data/
  customer_profile.csv
  change_tariff.csv
  traffic.csv
  arpu_monthly.csv
  dict_tariff.csv
  tariff_dictionary.csv
  feature_dictionary.csv
```

Затем нужно связать их с объектом окружения, который передаётся в
`Agent.act(env)`. Минимальный контракт окружения:

```python
env.customer_profile
env.tariffs
env.channels
env.remaining_budget
env.remaining_contacts
env.pilots_left
env.run_pilot(...)
```

При официальной проверке важно сохранить вызов `env.run_pilot(...)`, потому
что разведка является центральной частью задачи.

## Проверка перед демонстрацией

```powershell
py -3 -m py_compile agent.py db.py local_eval.py server.py make_submission.py
py -3 make_submission.py
```

В успешном результате должны быть:

```text
within_limits=True
invalid=0
```

Также нужно проверить dashboard: загрузить CSV, запустить агента и убедиться,
что в таблице отображаются все поля кампании, включая ARPU, data, calls,
текущий тариф, целевой тариф и канал.

## Статус проекта

В репозитории готова локальная end-to-end версия: база, агент, пилоты,
scoring, backend, dashboard, импорт CSV и генерация submission. Для финального
конкурсного score остаётся подключить официальный judge и оригинальные данные
организаторов; локальная модель не выдаёт официальный результат конкурса.
