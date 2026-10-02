Career Quest

Карьерный навигатор для сотрудников: **роль → цель → дефицит навыков → объяснимая рекомендация → активность → обновлённый прогресс**.

Проект хакатона Hackalem, трек «Управление». Приложение связывает разрозненные HR-мероприятия с карьерной целью сотрудника, а HR показывает общую картину развития команды.

## Что работает в коде

- Spring Boot MVC-приложение с многослойной архитектурой config/controller/dao/model/service.
- Импорт настоящего синтетического датасета заказчика в реляционную БД при первом запуске.
- Профиль сотрудника и изменение карьерной цели, включая переход между ролями.
- Учёт завершений после последней оценки навыков; критические навыки и процент готовности.
- До трёх рекомендаций с объяснением дефицита, соответствия роли/грейду и истории формата.
- Проверка prerequisite, расписания, обязательности и уже пройденных активностей.
- Симуляция завершения, сохранение истории, повторный расчёт навыков и рекомендаций.
- XP, уровень и три вычисляемых бейджа.
- HR-аналитика: частые gaps, средняя готовность, отсутствие цели/следующего шага, статусы.
- Form login, BCrypt, права HR/EMPLOYEE, CSRF и ограничение доступа к чужому профилю.
- Переключение русского, казахского и английского интерфейса.
- История с серверной пагинацией, централизованные ошибки, Log4j2.
- Unit-тесты с Mockito, H2-интеграционные тесты DAO, MockMvc-тесты страниц и безопасности.

Названия курсов, ролей и навыков сохранены на языке исходного датасета. UI-подписи и объясняющие шаблоны переведены.

## Технологии

Java 17; Spring Boot 3.5.6; Spring MVC; Spring Security; Spring JDBC/JdbcTemplate; Thymeleaf; MySQL; H2 для demo/tests; Jackson; Apache Commons CSV; Log4j2; JUnit 5; Mockito; MockMvc; JaCoCo; Maven.

**Внешние OpenAI/NVIDIA API и LLM сейчас не подключены.** Recommendation Engine — детерминированные правила и scoring. Ключи API для запуска не требуются. Созданный ранее описательный README не являлся доказательством реализации; этот README относится к исходникам в данном архиве.

## Быстрый запуск без MySQL

Нужны Java 17+ и Maven 3.6.3+. В комплекте Maven Wrapper 3.9.9: если mvn не установлен, замените mvn на ./mvnw (Windows: mvnw.cmd). Первый запуск требует интернет для зависимостей.

Запускать команды нужно из корневой папки проекта, где лежит `pom.xml`.

Пример для macOS, если проект лежит в IntelliJ IDEA Projects:

```bash
cd /Users/yeldarskiy/IdeaProjects/hack-62902277-aceforce
ls -la
```

В списке должны быть:

```text
pom.xml
src
mvnw
.mvn
README.md
```

Если проект распакован как `career-quest`, команда будет другой:

```bash
cd /Users/yeldarskiy/IdeaProjects/career-quest
```

После этого можно запускать тесты и сервер:

```bash
mvn clean test
mvn spring-boot:run -Dspring-boot.run.profiles=demo
```

Если Maven не установлен, используйте Maven Wrapper:

```bash
chmod +x mvnw
./mvnw clean test
./mvnw spring-boot:run -Dspring-boot.run.profiles=demo
```

Если `./mvnw` выдаёт ошибку `cannot read distributionUrl property in ./.mvn/wrapper/maven-wrapper.properties`, значит при копировании проекта потерялась скрытая папка `.mvn`. В этом случае проще запустить через установленный Maven:

```bash
brew install maven
mvn clean test
mvn spring-boot:run -Dspring-boot.run.profiles=demo
```

Открыть [http://localhost:8080](http://localhost:8080).

Только для локального demo-профиля:

| Логин | Пароль | Доступ |
|---|---|---|
| hr | CareerDemo123! | Все сотрудники и HR dashboard |
| employee | CareerDemo123! | Только E0001 |

H2 demo хранит данные в памяти: после остановки они сбрасываются. Демо-аккаунты и пароль нельзя использовать при публичном размещении.

## Данные для входа и проверки

Основной адрес приложения после запуска:

```text
http://localhost:8080
```

Страница входа:

```text
http://localhost:8080/login
```

Демо-профиль запуска:

```bash
mvn spring-boot:run -Dspring-boot.run.profiles=demo
```

или:

```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=demo
```

Учётные записи для локальной демонстрации:

| Роль | Логин | Пароль | Что можно делать |
|---|---|---|---|
| HR | hr | CareerDemo123! | Смотреть всех сотрудников, HR-аналитику, менять выбранного сотрудника на dashboard |
| Employee | employee | CareerDemo123! | Смотреть только профиль сотрудника E0001 и выполнять его рекомендации |

Основные страницы:

| URL | Назначение | Доступ |
|---|---|---|
| `/` | Главный dashboard сотрудника | HR, Employee |
| `/login` | Страница авторизации | Все |
| `/activities` | История активностей сотрудника | HR, Employee |
| `/achievements` | XP, уровень и бейджи | HR, Employee |
| `/hr` | HR dashboard и аналитика | Только HR |
| `/api/data/summary` | Проверка количества импортированных данных | Только HR |
| `/api/hr/analytics` | JSON с HR-аналитикой | Только HR |

Быстрая проверка данных после входа как HR:

```text
http://localhost:8080/api/data/summary
```

Ожидаемый смысл ответа:

```text
employees = 200
skills = 60
profiles = 32
events = 40
historyRecords = 2743
```

Проверочный сотрудник для демонстрации:

```text
E0001 - Marat Yessenov
Current role: Backend Engineer Junior
Default target: Backend Engineer Middle
```

Что показать жюри в первую очередь:

1. Войти как `hr`.
2. Открыть `/` и выбрать сотрудника `E0001`.
3. Показать текущую роль, целевую роль, процент готовности и skill gaps.
4. Показать рекомендованное мероприятие и объяснение, почему оно выбрано.
5. Нажать завершение рекомендации.
6. Показать, что XP вырос, история пополнилась, прогресс и рекомендации пересчитались.
7. Открыть `/achievements` и показать уровень/бейджи.
8. Открыть `/activities` и показать историю с пагинацией.
9. Открыть `/hr` и показать HR-аналитику.
10. Переключить язык RU / KK / EN.
11. Выйти и войти как `employee`; показать, что HR-раздел недоступен.

Данные авторизации актуальны только для demo-профиля. При запуске с MySQL demo-пользователи создаются только если включить переменные `DEMO_USERS=true` и `DEMO_PASSWORD`.

## Запуск с MySQL

MySQL — профиль по умолчанию. Можно использовать собственный MySQL 8 или приложенный compose.yaml.

1. Задайте локальные пароли (не добавляйте их в Git):

```bash
export DB_PASSWORD='replace-with-your-own-password'
export MYSQL_ROOT_PASSWORD='replace-with-another-password'
docker compose up -d
docker compose ps
```

Дождитесь healthy. Compose публикует MySQL только на 127.0.0.1.

2. Для локальной демонстрации создайте тестовые учётные записи с собственным паролем:

```bash
export DEMO_USERS=true
export DEMO_PASSWORD='replace-with-at-least-12-characters'
export DB_USERNAME=career
mvn spring-boot:run -Dspring-boot.run.profiles=mysql
```

Логины будут hr и employee; пароль — ваш DEMO_PASSWORD. Пароли записываются в app_user только в виде BCrypt-хешей. Если учётные записи уже существуют, повторный запуск их пароль не меняет.

3. Внешняя база: задайте DB_URL, DB_USERNAME, DB_PASSWORD. База career_quest должна существовать, пользователь должен иметь права на создание таблиц и работу с данными. Приложение создаёт таблицы, но не удаляет существующие данные.

```bash
export DB_URL='jdbc:mysql://localhost:3306/career_quest?useUnicode=true&characterEncoding=UTF-8&serverTimezone=UTC'
```

4. При DEMO_USERS=false автоматически учётные записи не создаются. Для эксплуатации их нужно отдельно безопасно подготовить в app_user; UI управления пользователями в этой версии нет.

## Сборка JAR

```bash
mvn clean package
java -jar target/career-quest-1.0.0.jar --spring.profiles.active=demo
```

## Архитектура и файлы

```text
career-quest/
  pom.xml
  README.md
  index.html                  # автономный макет дизайна, не рабочее приложение
  compose.yaml
  .gitignore
  docs/
    ER-diagram.md
    ARCHITECTURE.md
  logs/                       # log4j2 создаёт журнал; содержимое игнорируется
  src/main/java/kz/hackalem/careerquest/
    CareerQuestApplication.java
    config/
    controller/support/
    dao/impl/
    exception/
    interceptor/
    model/
    service/
    util/
  src/main/resources/
    application.properties
    application-demo.properties
    application-mysql.properties
    log4j2.xml
    db/schema.sql
    db/schema-h2.sql
    db/data.sql
    data/                     # JSON/CSV заказчика
    i18n/messages.properties
    i18n/messages_ru.properties
    i18n/messages_kk.properties
    i18n/messages_en.properties
    templates/
      auth/ dashboard/ activities/ achievements/ hr/ error/ fragments/
    static/css/app.css
    static/js/app.js
  src/test/java/               # unit + DAO/MockMvc integration tests
  src/test/resources/application.properties
  target/                     # генерируется Maven; не входит в исходники
```

[ER-диаграмма](docs/ER-diagram.md) · [Архитектура и соответствие капстоуну](docs/ARCHITECTURE.md).

Для исполняемого Boot JAR web.xml и WEB-INF не нужны: DispatcherServlet настраивается автоматически. Точка входа UI — MVC dashboard/index.html. Корневой index.html — только предварительный просмотр дизайна.

## Данные и импорт

| Файл | Содержание |
|---|---|
| skills.json | 60 навыков, 32 профиля (8 ролей × 4 грейда) |
| employees.json | 200 сотрудников |
| events.json | 40 мероприятий |
| activity_history.csv | 2 743 записи |

Все данные синтетические. Расчётная дата — **2026-10-01**, не дата компьютера. Исходные уровни employee_skill — оценка на last_review_date.

Импорт транзакционный, один раз на пустую базу. При повторном запуске marker dataset_import предотвращает дубли. Для нового набора укажите DATASET_LOCATION=file:/absolute/path/to/dataset/ и используйте отдельную пустую БД (или перезапустите demo). Формат должен соответствовать исходному README заказчика. Не надо редактировать идентификаторы в Java. Неправильные внешние ключи приводят к откату импорта.

schema.sql — MySQL-совместимая схема. schema-h2.sql — схема тестовой БД в режиме MySQL. data.sql не содержит тысяч строк и открытых паролей: бизнес-данные импортирует DatasetImportService из исходных файлов.

## Расчёт готовности

```text
gap(skill) = max(required - effective, 0)
progress = 100 × sum(min(effective, required)) / sum(required)
```

Отсутствующий навык равен 0. Завершения после last_review_date применяются в хронологическом порядке. Прирост ограничен gain/max_level/шкалой 0–5 и не снижает текущий уровень.

Если career_goal отсутствует, выбирается следующий грейд той же роли. Для Lead используется текущий Lead-профиль. Для межролевой цели сравнение проводится с требованиями целевой роли.

Процент — индикатор развития, не автоматическое решение о повышении. Критические дефициты выделяются отдельно.

## Рекомендации

Фильтры: mandatory=false; релевантная текущая или целевая роль и грейд; выполненные prerequisites; реальное сокращение gap; актуальная сессия либо self_paced/уже начатая активность; отсутствие завершения (кроме EV_036).

```text
score = 4 × impact + 3 × criticalImpact + 2
      + min(2, completedSameFormat × 0.25)
      - min(2, droppedOrMissedSameFormat × 0.5)
      - min(2, durationHours / 20)
      + (alreadyStarted ? 1 : 0)
```

impact — фактически сокращаемое число уровней навыков с учётом max_level и требований цели. При равном score сортировка по event_id обеспечивает воспроизводимость.
Выбор политики — Strategy (RecommendationScoringPolicy). В UI показаны факторы объяснения, а не выдуманная «вероятность повышения».

В исходном CSV нет отдельной completion_date: поле date используется как временной ориентир завершения. В демо при нажатии «Завершить» используется дата среза.

## Безопасность и сохранение

- Все пользовательские SQL-параметры передаются через JdbcTemplate bindings.
- Строка сотрудника блокируется на время завершения и смены цели.
- Повторный requestId не начисляет XP дважды.
- За каждое completed — 100 XP; level = 1 + completed / 3 (целочисленно).
- Бейджи: 1, 5, 10 завершений. XP не участвует в формуле readiness.
- История и цели сохраняются в MySQL и переживают перезапуск.
- CSRF нельзя отключать для обхода ошибок API. POST требует токен из пользовательской сессии.
- Запросы логируются без тела, query string, паролей и API-ключей.

## Как проверить

1. Запустить demo и войти как hr.
2. Проверить /api/data/summary: 200 / 60 / 32 / 40 / 2743.
3. На dashboard выбрать E0001 — Marat Yessenov; текущая роль Backend Engineer Junior, цель Middle.
4. Посмотреть gaps, критические навыки и объяснение первой рекомендации.
5. Завершить рекомендованную активность. Прогресс растёт, XP добавляется, рекомендации пересчитываются.
6. Обновить страницу: результат остаётся. В MySQL сохраняется и после перезапуска приложения.
7. Сменить цель или выбрать другого сотрудника, включая цель в другой роли.
8. Переключить RU / KK / EN.
9. Проверить историю и pagination, достижения, HR analytics.
10. Войти как employee: HR недоступен, чужой employeeId возвращает 403.

## Тесты

```bash
mvn clean test
```

Результаты JUnit: target/surefire-reports/.
Отчёт покрытия JaCoCo создаётся уже на фазе test: target/site/jacoco/index.html.
Тесты по умолчанию используют H2, настоящая MySQL для mvn clean test не требуется.

Проверено при подготовке архива: **60 тестов, 0 failures, 0 errors, 0 skipped**. Покрытие строк: общее 98,7%, service 99,4%, dao/impl 100%. Это метрика выполненных строк, не гарантия отсутствия ошибок.

После mvn package можно дополнительно запустить node scripts/smoke.cjs (Node.js 18+): скрипт поднимает JAR на порту 18080, проверяет login, датасет и рабочие страницы, затем останавливает приложение.
Подробности и границы проверки — [docs/VERIFICATION.md](docs/VERIFICATION.md).

Есть отдельные тестовые классы для конкретных production-классов; DAO проверяются интеграционно на SQL, бизнес-сервисы — изолированно с Mockito, конфигурация и контроллеры — через Spring/MockMvc. Для интерфейса без реализации unit-тест не создаётся искусственно.

КАК ЗАПУСТИТЬ ПРОЕКТ ЛОКАЛЬНО?

cd /Users/yeldarskiy/IdeaProjects/hack-62902277-aceforce
mvn spring-boot:run -Dspring-boot.run.profiles=demo

hr
CareerDemo123!
employee
CareerDemo123!
