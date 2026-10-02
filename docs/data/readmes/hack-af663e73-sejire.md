# Умный подбор подрядчиков

Авторы: Alexey Azovskiy, Amir Meirmanov.

Репозиторий закрытый: [github.com/BAITC-Hacks/hack-af663e73-sejire](https://github.com/BAITC-Hacks/hack-af663e73-sejire). Постоянного публичного сайта нет. Проверяющий получает доступ к репозиторию от авторов, клонирует его и запускает сервис на своём компьютере. Пока окно запуска открыто, страница доступна по адресу http://127.0.0.1:8080 , админ-панель — http://127.0.0.1:8080/admin .

Сервис рекомендует подрядчиков по анонимизированному каталогу. Бронирования, оплаты, уведомлений подрядчикам и личных кабинетов заказчиков нет. Внешние API, языковые модели и ключи не используются.

## Данные

В `data/contractors.csv` 66 профилей. Колонки:

`id`, `anon_name`, `categories`, `city`, `city_imputed`, `synthetic`, `price_from_kzt`, `price_imputed`, `event_formats`, `languages`, `max_hours`, `busy_dates`, `description`.

- `categories` — кто подрядчик.
- `event_formats` — для каких событий он работает: свадьба, той, корпоратив, конференция, юбилей, день рождения.
- `languages` — язык работы: русский, казахский, английский.
- `city` — Алматы, Астана или Зарубежье.
- `price_from_kzt` — цена «от» в тенге, не вилка.
- `max_hours` — максимум часов на площадке. Пустое значение значит, что ограничение по присутствию неприменимо.
- `busy_dates` — конкретные занятые даты в диапазоне 23.09.2026–31.12.2026, через `|`.
- `synthetic`, `city_imputed`, `price_imputed` — признаки синтетического профиля или значения, проставленного при подготовке датасета.

Поля вроде числа выполненных работ, вместимости гостей и бюджетной вилки в каталоге нет, и подбор их не использует. Если цена пустая, профиль не называется подходящим по бюджету: он остаётся в списке отказов с причиной «цена не указана».

## Как устроен подбор

Форма принимает город, дату, тип мероприятия, категорию подрядчика, бюджет в тенге и необязательные длительность и язык.

В результаты попадает только профиль, у которого:

- город совпадает;
- выбранная категория есть в `categories`;
- выбранный тип есть в `event_formats`;
- цена известна и `price_from_kzt` не выше бюджета;
- выбранной даты нет в `busy_dates`;
- если язык задан, он есть в `languages`;
- если длительность задана и `max_hours` не пустой, лимит не меньше этой длительности.

Пустой `max_hours` по длительности никого не отсекает.

Ответ содержит не больше трёх карточек. Порядок детерминированный: наименьшая цена «от», при равной цене — `id`. Это порядок по цене, не оценка качества. Над карточками написано, сколько профилей прошло фильтр и сколько показано. Если город не содержит выбранной категории, исход отдельный: указано, в каких других городах категория есть. Если категория в городе есть, но никто не прошёл, перечислены все отказы и причина каждого: формат, неизвестная цена, бюджет, занятая дата, язык или длительность.

Текст карточки собирается из полей этого профиля и параметров запроса: город, категория, цена относительно бюджета, тип, точная дата, языки, лимит часов. Первое предложение описания добавляется как цитата. Для синтетического профиля и для восстановленных города или цены добавляется явная пометка. Восстановленная цена не выдаётся за подтверждённую.

Интерфейс подбора и админки переключается на русский, казахский и английский. Названия значений каталога остаются такими, как они записаны в данных; подписи полей переводятся.

## Как жюри запускает проект

Репозиторий закрытый. Авторы заранее открывают доступ аккаунту GitHub проверяющего. Без этого приглашения клонирование завершится ошибкой доступа. Отдельный хостинг и туннель не нужны: сервис поднимается на компьютере проверяющего и работает, пока открыто окно терминала.

Нужен Git и Python 3.10 или новее. Сторонние пакеты не ставятся: хватает стандартной библиотеки Python.

1. Установите [Git](https://git-scm.com/downloads) и [Python](https://www.python.org/downloads/). На Windows в установщике Python отметьте Add python.exe to PATH. Проверка в новом окне терминала: `python --version` показывает 3.10 или выше. Если `python` открывает магазин Microsoft, закройте его и установите Python с python.org.
2. Клонируйте репозиторий и перейдите в его папку. GitHub запросит вход: используйте аккаунт, которому выдан доступ.

```
git clone https://github.com/BAITC-Hacks/hack-af663e73-sejire.git
cd hack-af663e73-sejire
```

3. Придумайте пароль администратора не короче 6 символов. В репозитории пароля нет, программа его не печатает и не записывает в журнал. Подставьте свой пароль вместо `ваш-пароль` и запустите сервис из папки проекта.

PowerShell:

```
$env:ADMIN_PASSWORD="ваш-пароль"
python app.py
```

Командная строка Windows:

```
set ADMIN_PASSWORD=ваш-пароль
python app.py
```

macOS и Linux:

```
ADMIN_PASSWORD='ваш-пароль' python3 app.py
```

Окно не закрывайте. Строка «Сервис слушает порт 8080» означает, что запуск прошёл. Если пароль не задан и файла `data/admin.json` ещё нет, процесс сразу остановится и напишет, что нужна переменная `ADMIN_PASSWORD`.

4. Откройте в браузере http://127.0.0.1:8080 . При первом запуске каталог из 66 профилей сам загружается из `data/contractors.csv`. Готовые запросы из раздела «Проверенные запросы» вводятся в форму вручную. Админ-панель: http://127.0.0.1:8080/admin . Логин `admin`. Пароль — тот, который вы подставили в `ADMIN_PASSWORD`. Логин можно сменить переменной `ADMIN_USER` до первого запуска.
5. Остановка: в окне терминала нажмите Ctrl+C. После этого страница перестаёт открываться. Следующий запуск из той же папки снова поднимает сервис. Файл `data/admin.json` уже создан, поэтому пароль повторно задавать не нужно: действует первый. В файле лежит только хеш scrypt, не сам пароль. Смена пароля есть в админке: текущий, новый и повтор. Чтобы задать пароль заново через переменную, удалите `data/admin.json` и перед запуском снова укажите `ADMIN_PASSWORD`.

Файлы `data/admin.json` и `data/contractors.db` создаются на компьютере проверяющего и в git не входят. Больше 8 неудачных попыток входа с одного адреса за 10 минут временно блокируются. Сессия и этот счётчик пропадают после остановки процесса. Cookie сессии живёт 12 часов и имеет флаги `HttpOnly` и `SameSite=Lax`.

## Каталог

В админке можно добавить один профиль, изменить его и удалить после подтверждения. Новая запись без `id` сохраняется как синтетическая.

CSV загружается в два шага. После выбора файла показывается предпросмотр: какие строки будут добавлены, какие обновлены, какие пропущены как повтор `id` или ошибка. Запись начинается только после подтверждения. Повторный импорт той же строки с тем же `id` обновляет её и не создаёт копию. Поддерживаются UTF-8 с BOM, кавычки, запятые и переносы внутри полей. Флаги и `busy_dates` сохраняются. Если при разборе файла возникает ошибка строки, она попадает в отчёт и не записывается; уже разобранные корректные строки этой загрузки сохраняются вместе с отчётом. Неожиданный сбой откатывает транзакцию загрузки, открытой этим запросом.

После добавления и импорта списки городов и категорий на главной читаются из каталога заново.

## Проверенные запросы

Эти четыре запроса проверены по загруженным 66 профилям. Их можно ввести в форму на главной.

1. Плотная категория. Алматы, 14.10.2026, корпоратив, ведущий, бюджет 1 500 000. В городе 10 ведущих, проходят 7. Показаны три с наименьшей ценой: Куррапика, 500 000 тг, `HK-88430`; Мицури Канроджи, 650 000 тг, `HK-44923`; Кики, 900 000 тг, `HK-35215`. Дороже и тоже проходят Сон Гоку, Буллма, Хаул и Джинбей. Не проходят Аня Форджер (дата занята), Софи Хаттер (цена от 2 000 000 тг) и Эмилия (нет формата «корпоратив»).
2. Редкая категория. Алматы, 14.10.2026, свадьба, флорист, бюджет 500 000. В городе 2 флориста, проходит 1: Тихиро Огино, 250 000 тг, `HK-90001`, синтетический профиль, лимит часов пустой. Тони Тони Чоппер не проходит: 14.10.2026 есть в занятых датах.
3. Тот же запрос, что в пункте 1, но дата 12.12.2026. Категория в городе есть, проходят 0 из 10. У восьми дата занята, у Софи Хаттер цена выше бюджета, у Эмилии нет формата «корпоратив».
4. Пустой результат другого вида. Астана, 14.11.2026, конференция, ресторан, бюджет 2 000 000. В Астане ресторанов нет. Категория есть в Алматы.

Повтор любого из этих запросов возвращает тот же набор и тот же порядок.

## Ограничения

Каталог анонимный и покрывает занятость только внутри своего диапазона дат. Цитата в карточке — первое предложение описания, не отдельный отзыв. Сортировка не измеряет качество. Синтетические профили и восстановленные город или цена помечены и не выдаются за подтверждённые сведения. Страница доступна только пока на компьютере проверяющего запущен `python app.py`. Сессии и счётчик входа не переживают остановку процесса.

## Проверки

```
python -m unittest test_match.py
```

Файл `test_match.py` проверяет загрузку 66 строк и флаги, фильтры, устойчивый порядок по цене и `id`, различие «категории нет» и «все отсеяны», занятые даты, пустой лимит часов, неизвестную цену, импорт исходной схемы CSV, сохранение флагов и обновление по тому же `id`.

---

# Мердігерлерді ақылды іріктеу

Авторлар: Alexey Azovskiy, Amir Meirmanov.

Репозиторий жабық: [github.com/BAITC-Hacks/hack-af663e73-sejire](https://github.com/BAITC-Hacks/hack-af663e73-sejire). Тұрақты жария сайт жоқ. Тексеруші авторлардан репозиторийге қол жеткізеді, оны көшіріп алады және сервисті өз компьютерінен іске қосады. Іске қосу терезесі ашық тұрғанда бет мына мекенжайда ашылады: http://127.0.0.1:8080 , әкімші панелі — http://127.0.0.1:8080/admin .

Сервис анонимді каталог бойынша мердігер ұсынады. Брондау, төлем, мердігерге хабарлама және тапсырыс берушінің жеке кабинеті жоқ. Сыртқы API, тілдік модель және кілт қолданылмайды.

## Деректер

`data/contractors.csv` файлында 66 профиль. Бағандар:

`id`, `anon_name`, `categories`, `city`, `city_imputed`, `synthetic`, `price_from_kzt`, `price_imputed`, `event_formats`, `languages`, `max_hours`, `busy_dates`, `description`.

- `categories` — мердігер кім.
- `event_formats` — қай іс-шараға жұмыс істейді: свадьба, той, корпоратив, конференция, юбилей, день рождения.
- `languages` — жұмыс тілі: русский, казахский, английский.
- `city` — Алматы, Астана немесе Зарубежье.
- `price_from_kzt` — теңгедегі бастапқы баға, аралық емес.
- `max_hours` — алаңдағы сағат шегі. Бос мән шектеу қолданылмайтынын білдіреді.
- `busy_dates` — 23.09.2026–31.12.2026 аралығындағы нақты бос емес күндер, `|` арқылы.
- `synthetic`, `city_imputed`, `price_imputed` — синтетикалық профиль немесе дайындау кезінде қойылған мән.

Орындалған жұмыс саны, қонақ сыйымдылығы және бюджет аралығы каталогта жоқ, іріктеу оларды қолданбайды. Баға бос болса, профиль бюджетке сай деп аталмайды: ол «баға көрсетілмеген» себебімен бас тарту тізімінде қалады.

## Іріктеу қалай жұмыс істейді

Пішін қала, күн, іс-шара түрі, мердігер санаты, теңгедегі бюджет және міндетті емес ұзақтық пен тілді қабылдайды.

Нәтижеге тек мына шарттардың бәрі орындалған профиль кіреді:

- қала сәйкес;
- таңдалған санат `categories` ішінде;
- таңдалған түрі `event_formats` ішінде;
- баға белгілі және `price_from_kzt` бюджеттен аспайды;
- таңдалған күн `busy_dates` ішінде жоқ;
- тіл берілсе, ол `languages` ішінде бар;
- ұзақтық берілсе және `max_hours` бос болмаса, шек осы ұзақтықтан кем емес.

Бос `max_hours` ұзақтық бойынша ешкімді шығармайды.

Жауапта ең көбі үш карточка. Рет тұрақты: ең төмен бастапқы баға, баға тең болса `id`. Бұл баға реті, сапа бағасы емес. Карточкалардың үстінде фильтрден қанша профиль өткені және қаншасы көрсетілгені жазылады. Қалада таңдалған санат болмаса, ол басқа нәтиже: санат қай қалаларда бар екені көрсетіледі. Санат қалада бар, бірақ ешкім өтпесе, барлық бас тарту және әрқайсының себебі тізіледі: формат, белгісіз баға, бюджет, бос емес күн, тіл немесе ұзақтық.

Карточка мәтіні осы профиль өрістері мен сұрау параметрлерінен құралады: қала, санат, бюджетке қатысты баға, түрі, нақты күн, тілдер, сағат шегі. Сипаттаманың бірінші сөйлемі дәйексөз ретінде қосылады. Синтетикалық профильге және қалпына келтірілген қалаға немесе бағаға анық белгі қойылады. Қалпына келтірілген баға расталған баға ретінде көрсетілмейді.

Іріктеу және әкімші интерфейсі орысша, қазақша және ағылшынша ауысады. Каталог мәндері деректе жазылғанындай қалады, өріс атаулары аударылады.

## Қазылар алқасы жобаны қалай іске қосады

Репозиторий жабық. Авторлар тексерушінің GitHub аккаунтына алдын ала қол жеткізу береді. Шақырусыз клондау қолжетімсіздік қатесімен аяқталады. Бөлек хостинг пен туннель керек емес: сервис тексерушінің компьютерінен көтеріледі және терминал терезесі ашық тұрғанда жұмыс істейді.

Git және Python 3.10 не одан жаңасы керек. Бөгде пакеттер орнатылмайды: Python стандартты кітапханасы жетеді.

1. [Git](https://git-scm.com/downloads) және [Python](https://www.python.org/downloads/) орнатыңыз. Windows жүйесінде Python орнатқышында Add python.exe to PATH белгісін қойыңыз. Жаңа терминал терезесіндегі тексеру: `python --version` 3.10 не одан жоғары нұсқаны көрсетеді. `python` Microsoft дүкенін ашса, оны жауып, Python-ды python.org сайтынан орнатыңыз.
2. Репозиторийді клондаңыз және оның папкасына кіріңіз. GitHub кіруді сұрайды: қол жеткізу берілген аккаунтты қолданыңыз.

```
git clone https://github.com/BAITC-Hacks/hack-af663e73-sejire.git
cd hack-af663e73-sejire
```

3. Кемінде 6 таңбадан тұратын әкімші құпиясөзін ойлап табыңыз. Репозиторийде құпиясөз жоқ, бағдарлама оны басып шығармайды және журналға жазбайды. `ваш-пароль` орнына өз құпиясөзіңізді қойып, сервисті жоба папкасынан іске қосыңыз.

PowerShell:

```
$env:ADMIN_PASSWORD="ваш-пароль"
python app.py
```

Windows командалық жолы:

```
set ADMIN_PASSWORD=ваш-пароль
python app.py
```

macOS және Linux:

```
ADMIN_PASSWORD='ваш-пароль' python3 app.py
```

Терезесін жаппаңыз. «Сервис слушает порт 8080» жолы іске қосу өткенін білдіреді. Құпиясөз берілмесе және `data/admin.json` файлы әлі жоқ болса, процесс бірден тоқтайды және `ADMIN_PASSWORD` айнымалысы керек екенін жазады.

4. Браузерде http://127.0.0.1:8080 ашыңыз. Алғашқы іске қосуда 66 профильдік каталог `data/contractors.csv` файлынан өзі жүктеледі. «Тексерілген сұраулар» бөліміндегі дайын сұраулар пішінге қолмен енгізіледі. Әкімші панелі: http://127.0.0.1:8080/admin . Логин `admin`. Құпиясөз — `ADMIN_PASSWORD` ішіне қойғаныңыз. Логинді алғашқы іске қосуға дейін `ADMIN_USER` айнымалысымен ауыстыруға болады.
5. Тоқтату: терминал терезесінде Ctrl+C басыңыз. Осыдан кейін бет ашылмайды. Сол папкадан келесі іске қосу сервисті қайта көтереді. `data/admin.json` файлы жасалған, сондықтан құпиясөзді қайта беру керек емес: біріншісі қолданылады. Файлда тек scrypt хеші жатады, құпиясөздің өзі емес. Құпиясөзді панелде ауыстыруға болады: ағымдағы, жаңа және қайталау. Құпиясөзді айнымалы арқылы қайта беру үшін `data/admin.json` файлын жойып, іске қосу алдында `ADMIN_PASSWORD` көрсетіңіз.

`data/admin.json` және `data/contractors.db` файлдары тексерушінің компьютерінен жасалады және git-ке кірмейді. Бір мекенжайдан 10 минутта 8-ден артық сәтсіз кіру уақытша бұғатталады. Сессия мен бұл есептегіш процесті тоқтатқанда жоғалады. Сессия cookie-і 12 сағат сақталады және `HttpOnly`, `SameSite=Lax` белгілері бар.

## Каталог

Әкімші панелінде бір профиль қосуға, өзгертуге және растаудан кейін жоюға болады. `id` жоқ жаңа жазба синтетикалық болып сақталады.

CSV екі қадаммен жүктеледі. Файл таңдалған соң алдын ала қарау шығады: қай жолдар қосылады, қайсысы жаңартылады, қайсысы қайталанған `id` немесе қате ретінде өткізіледі. Жазу тек растаудан кейін басталады. Сол `id` бар жолды қайта импорттау оны жаңартады және көшірме жасамайды. BOM бар UTF-8, тырнақша, үтір және өріс ішіндегі жол ауыстыру қолдау табады. Белгілер мен `busy_dates` сақталады. Жол қатесі есепке түседі және жазылмайды; осы жүктеудің дұрыс жолдары есеппен бірге сақталады. Күтпеген ақау осы сұрау ашқан транзакцияны кері қайтарады.

Қосқаннан және импорттан кейін басты беттегі қала мен санат тізімдері каталогтан қайта оқылады.

## Тексерілген сұраулар

Осы төрт сұрау жүктелген 66 профиль бойынша тексерілген. Оларды басты беттегі пішінге енгізуге болады.

1. Жиі санат. Алматы, 14.10.2026, корпоратив, ведущий, бюджет 1 500 000. Қалада 10 жүргізуші, 7-еуі өтеді. Ең төмен бағамен үшеуі көрсетіледі: Куррапика, 500 000 тг, `HK-88430`; Мицури Канроджи, 650 000 тг, `HK-44923`; Кики, 900 000 тг, `HK-35215`. Қымбатырақ, бірақ өтетіндер: Сон Гоку, Буллма, Хаул, Джинбей. Өтпейтіндер: Аня Форджер (күн бос емес), Софи Хаттер (бастапқы баға 2 000 000 тг), Эмилия («корпоратив» түрі жоқ).
2. Сирек санат. Алматы, 14.10.2026, свадьба, флорист, бюджет 500 000. Қалада 2 флорист, 1-еуі өтеді: Тихиро Огино, 250 000 тг, `HK-90001`, синтетикалық профиль, сағат шегі бос. Тони Тони Чоппер өтпейді: 14.10.2026 бос емес күндерде бар.
3. 1-тармақтағы сұрау, бірақ күні 12.12.2026. Санат қалада бар, 10-нан 0-і өтеді. Сегізінің күні бос емес, Софи Хаттердің бағасы бюджеттен жоғары, Эмилияда «корпоратив» түрі жоқ.
4. Басқа бос нәтиже. Астана, 14.11.2026, конференция, ресторан, бюджет 2 000 000. Астанада мейрамхана жоқ. Санат Алматыда бар.

Осы сұраулардың кез келгенін қайталау сол жиынды және сол ретті береді.

## Шектеулер

Каталог анонимді және бос емес күндерді тек өз күн аралығында көрсетеді. Карточкадағы дәйексөз — сипаттаманың бірінші сөйлемі, бөлек пікір емес. Сұрыптау сапаны өлшемейді. Синтетикалық профильдер және қалпына келтірілген қала немесе баға белгіленеді және расталған дерек ретінде берілмейді. Бет тексерушінің компьютерінен `python app.py` іске қосылып тұрғанда ғана ашылады. Сессия мен кіру есептегіші процесті тоқтатқанда сақталмайды.

## Тексерулер

```
python -m unittest test_match.py
```

`test_match.py` 66 жол мен белгілердің жүктелуін, фильтрлерді, баға мен `id` бойынша тұрақты ретті, «санат жоқ» пен «бәрі шығарылды» айырмасын, бос емес күндерді, бос сағат шегін, белгісіз бағаны, бастапқы CSV схемасының импортын, белгілердің сақталуын және сол `id` бойынша жаңартуды тексереді.

---

# Smart contractor matching

Authors: Alexey Azovskiy, Amir Meirmanov.

The repository is private: [github.com/BAITC-Hacks/hack-af663e73-sejire](https://github.com/BAITC-Hacks/hack-af663e73-sejire). There is no permanent public site. A reviewer receives access from the authors, clones the repository, and starts the service on their own computer. While that window stays open, the page is at http://127.0.0.1:8080 and the admin panel is at http://127.0.0.1:8080/admin .

The service recommends contractors from an anonymized catalog. There is no booking, payment, contractor notification, or customer account. No external API, language model, or key is used.

## Data

`data/contractors.csv` has 66 profiles. Columns:

`id`, `anon_name`, `categories`, `city`, `city_imputed`, `synthetic`, `price_from_kzt`, `price_imputed`, `event_formats`, `languages`, `max_hours`, `busy_dates`, `description`.

- `categories` is who the contractor is.
- `event_formats` is which events they work: свадьба, той, корпоратив, конференция, юбилей, день рождения.
- `languages` is the working language: русский, казахский, английский.
- `city` is Алматы, Астана, or Зарубежье.
- `price_from_kzt` is a starting price in tenge, not a range.
- `max_hours` is the maximum hours on site. An empty value means a presence limit does not apply.
- `busy_dates` lists individual busy dates from 23.09.2026 to 31.12.2026, separated by `|`.
- `synthetic`, `city_imputed`, and `price_imputed` mark a synthetic profile or a value filled while the dataset was prepared.

Completed-job counts, guest capacity, and budget ranges are not in the catalog and are not used for matching. If the price is empty, the profile is not described as fitting the budget: it stays in the rejection list with the reason that the price is not stated.

## How matching works

The form takes a city, a date, an event type, a contractor category, a budget in tenge, and optional duration and language.

A profile is recommended only when:

- the city matches;
- the chosen category is in `categories`;
- the chosen type is in `event_formats`;
- the price is known and `price_from_kzt` is not above the budget;
- the chosen date is not in `busy_dates`;
- if a language is set, it is in `languages`;
- if a duration is set and `max_hours` is not empty, the limit is at least that duration.

An empty `max_hours` does not reject anyone for duration.

The response has at most three cards. The order is deterministic: lowest starting price, then `id` when prices are equal. This is a price order, not a quality score. Above the cards the page states how many profiles passed and how many are shown. If the city has no contractor of the chosen category, that is a separate outcome and the other cities that have the category are named. If the category exists in the city but nobody passed, every rejection is listed with its reason: format, unknown price, budget, busy date, language, or duration.

Card text is built from that profile’s fields and the query: city, category, price against the budget, type, exact date, languages, and hour limit. The first sentence of the description is added as a quotation. A synthetic profile and an imputed city or price get an explicit mark. An imputed price is not presented as confirmed.

The matching page and the admin page switch among Russian, Kazakh, and English. Catalog values stay as stored; field labels are translated.

## How the jury starts the project

The repository is private. The authors grant access to the reviewer’s GitHub account in advance. Without that invitation, cloning fails with an access error. No separate hosting or tunnel is required: the service runs on the reviewer’s computer for as long as the terminal window stays open.

Git and Python 3.10 or newer are required. No third-party packages are installed. The Python standard library is enough.

1. Install [Git](https://git-scm.com/downloads) and [Python](https://www.python.org/downloads/). On Windows, check Add python.exe to PATH in the Python installer. In a new terminal, `python --version` should show 3.10 or higher. If `python` opens the Microsoft Store, close it and install Python from python.org.
2. Clone the repository and enter its folder. GitHub asks you to sign in. Use the account that was granted access.

```
git clone https://github.com/BAITC-Hacks/hack-af663e73-sejire.git
cd hack-af663e73-sejire
```

3. Choose an admin password of at least 6 characters. The repository contains no password. The program does not print it and does not write it to the log. Replace `your-password` with your own password and start the service from the project folder.

PowerShell:

```
$env:ADMIN_PASSWORD="your-password"
python app.py
```

Windows Command Prompt:

```
set ADMIN_PASSWORD=your-password
python app.py
```

macOS and Linux:

```
ADMIN_PASSWORD='your-password' python3 app.py
```

Leave the window open. The line “Сервис слушает порт 8080” means the service started. If no password is set and `data/admin.json` does not exist yet, the process stops immediately and says that `ADMIN_PASSWORD` is required.

4. Open http://127.0.0.1:8080 in a browser. On the first start the catalog of 66 profiles is loaded from `data/contractors.csv`. The ready-made requests in “Checked requests” are entered in the form by hand. Admin panel: http://127.0.0.1:8080/admin . The login is `admin`. The password is the one you put in `ADMIN_PASSWORD`. The login can be changed with `ADMIN_USER` before the first start.
5. To stop, press Ctrl+C in the terminal. The page then stops opening. The next start from the same folder brings the service back. `data/admin.json` already exists, so the password does not need to be set again: the first one remains in effect. The file stores only a scrypt hash, not the password itself. The panel can change it: current password, new password, and a repeat. To set a password through the variable again, delete `data/admin.json` and set `ADMIN_PASSWORD` before starting.

`data/admin.json` and `data/contractors.db` are created on the reviewer’s computer and are not part of git. More than 8 failed login attempts from one address within 10 minutes are blocked for a while. The session and that counter disappear when the process stops. The session cookie lasts 12 hours and has the `HttpOnly` and `SameSite=Lax` flags.

## Catalog

The admin panel can add one profile, edit it, and delete it after confirmation. A new record without an `id` is stored as synthetic.

CSV upload has two steps. After the file is chosen, a preview shows which rows would be added, which would be updated, and which would be skipped as a repeated `id` or an error. Writing starts only after confirmation. Importing the same row with the same `id` updates it and does not create a copy. UTF-8 with BOM, quotes, commas, and line breaks inside fields are supported. Flags and `busy_dates` are kept. A bad row is reported and not written; the valid rows of that upload are saved together with the report. An unexpected failure rolls back the transaction opened by that request.

After an add or an import, the city and category lists on the main page are read from the catalog again.

## Checked requests

These four requests were checked against the loaded 66 profiles. They can be entered in the form on the main page.

1. Dense category. Almaty, 14.10.2026, корпоратив, Ведущий, budget 1 500 000. The city has 10 hosts and 7 pass. The three lowest prices are shown: Куррапика, 500 000 KZT, `HK-88430`; Мицури Канроджи, 650 000 KZT, `HK-44923`; Кики, 900 000 KZT, `HK-35215`. Сон Гоку, Буллма, Хаул, and Джинбей also pass at higher prices. Аня Форджер is busy, Софи Хаттер starts at 2 000 000 KZT, and Эмилия has no корпоратив format.
2. Rare category. Almaty, 14.10.2026, свадьба, Флорист, budget 500 000. The city has 2 florists and 1 passes: Тихиро Огино, 250 000 KZT, `HK-90001`, a synthetic profile with an empty hour limit. Тони Тони Чоппер does not pass: 14.10.2026 is in the busy dates.
3. The same request as item 1, but on 12.12.2026. The category exists in the city and 0 of 10 pass. Eight are busy, Софи Хаттер is above the budget, and Эмилия has no корпоратив format.
4. A different empty result. Astana, 14.11.2026, конференция, Ресторан, budget 2 000 000. Astana has no restaurants. The category exists in Almaty.

Repeating any of these requests returns the same set in the same order.

## Limitations

The catalog is anonymous and its occupancy covers only its own date range. The quotation on a card is the first sentence of the description, not a separate review. The sort does not measure quality. Synthetic profiles and an imputed city or price are marked and are not presented as confirmed facts. The page is available only while `python app.py` is running on the reviewer’s computer. Sessions and the login counter do not survive stopping the process.

## Checks

```
python -m unittest test_match.py
```

`test_match.py` checks loading 66 rows and the flags, the filters, a stable price-then-`id` order, the difference between “no category” and “everyone was rejected”, busy dates, an empty hour limit, an unknown price, import of the original CSV schema, preservation of flags, and an update of the same `id`.
