# hack-d3d1e752-zhanibek
Hackathon team repository for Zhanibek
http://127.0.0.1:8765/

let renderedExecution = null;
let currentLang = localStorage.getItem('windcast-language') || 'kk';
let latestStatus = null;

const L = {
  kk: {
    title: 'WindCast — Болжау панелі', pick: 'Файлды таңдау', upload: 'Жүктеу және есептеу', retry: 'Қайта жүктеу', loading: 'Жүктелуде…',
    run: 'Агентті іске қосу', idle: 'Бастау үшін ұйымдастырушының тарих файлын жүктеңіз.', queued: 'Файл қабылданды. Күнделікті болжамдарды есептеу басталады.', ingest: 'Турбина деректерінің құрылымы мен мәндері тексерілуде.', weather: 'Архивтік ауа райы деректері жүктелуде.', replay: 'Күнделікті болжамдар қайта есептелуде.', complete: n => `Қайта есептеу аяқталды: ${n} сағаттық нәтиже дайын.`, failed: 'Белгісіз қате.',
    running: 'ОРЫНДАЛУДА', error: 'ҚАТЕ', ready: 'ДАЙЫН', waiting: 'КҮТУДЕ', stepReady: 'ДАЙЫН', attention: 'Назар аудару қажет', dataWait: 'Дерек күтілуде',
    statusRunning: 'Орындалуда', stage: {ingest:'ДЕРЕКТІ ТЕКСЕРУ',weather_history:'АУА РАЙЫН ЖҮКТЕУ',replay:'БОЛЖАМДЫ ҚАЙТА ЕСЕПТЕУ',complete:'АЯҚТАЛДЫ',failed:'ҚАТЕ'},
    static: [
      ['.rail-label','ЖҰМЫС АЙМАҒЫ'],['.nav-item.active','Болжам панелі'],['.nav-item:nth-of-type(3)','Агент барысы'],['.nav-item:nth-of-type(4)','Нәтижелер'],['.source-pill','АРХИВТІ ҚАЙТА ЕСЕПТЕУ'],['.rail-meta','BAITC · HACKALEM AI<br>ЖЕЛ ЭНЕРГИЯСЫ / 2026'],['.crumb','БАСҚАРУ <span>/</span> БОЛЖАМ ПАНЕЛІ'],['.api-indicator','ECMWF IFS · АРХИВ'],['.hero-caption span','ҚАЗАҚСТАН · ЖЕЛ ЭНЕРГИЯСЫ'],['.page-heading .eyebrow','КҮНДЕЛІКТІ ҚАЙТА ЕСЕПТЕУ · АҚПАН 2026'],['.page-heading h1','Жел энергиясын <em>болжау</em>'],['.page-heading p','Балқаш маңындағы екі турбинаның сағаттық өндіріс болжамы. Әр күн үшін сол сәтте қолжетімді ауа райы архиві қолданылады.'],['#runButton','<span>↻</span> Агентті іске қосу'],
      ['.stat-label:nth-child(1)','ҚАЙТА ЕСЕПТЕУ КЕЗЕҢІ'],['.stat-card:nth-child(1) .stat-value','28 <small>күн</small>'],['.stat-card:nth-child(1) .stat-foot','2026 Ж. 1–28 АҚПАН'],['.stat-card:nth-child(2) .stat-label','БОЛЖАМ КӨКЖИЕГІ'],['.stat-card:nth-child(2) .stat-value','24–48 <small>сағ</small>'],['.stat-card:nth-child(2) .stat-foot','САҒАТ САЙЫН · МЕРЗІМІМЕН СӘЙКЕС'],['.stat-card:nth-child(3) .stat-label','ТУРБИНАЛАР'],['.stat-card:nth-child(3) .stat-value','02 <small>дана</small>'],['.stat-card:nth-child(3) .stat-foot','43.6452°С · 78.5356°Ш'],['.stat-card:nth-child(4) .stat-label','АГЕНТ КҮЙІ'],
      ['.upload-panel .eyebrow','БАСТАПҚЫ ДЕРЕКТЕР'],['.upload-panel h2','Турбина тарихын қосу'],['.upload-panel .step-tag','1-ҚАДАМ'],['.upload-panel .panel-copy','Ұйымдастырушы берген 2023 жылғы наурыздан 2026 жылғы қаңтарға дейінгі сағаттық өлшемдерді жүктеңіз. CSV, XLSX және XLSM файлдары жарайды.'],['.dropzone strong','Файлды осында сүйреңіз немесе <u>таңдаңыз</u>'],['.dropzone small','UTF-8 CSV не Excel · ең көбі 80 МБ'],['.schema-note span:last-child','Міндетті бағандар: уақыт белгісі, турбина ID, жел жылдамдығы, нормаланған қуат және температура. <a href="/template_observations.csv" download>CSV үлгісін алу ↗</a>'],['#uploadHint','Нақты болжам жасау үшін ұйымдастырушының бастапқы деректері қажет.'],
      ['.agent-panel .eyebrow','АВТОНОМДЫ ЖҰМЫС АҒЫНЫ'],['.agent-panel h2','Агент жұмысы'],['.agent-step:nth-child(1) strong','Деректерді тексеру'],['.agent-step:nth-child(1) small','Бағандар · мәндер ауқымы · UTC уақыты'],['.agent-step:nth-child(2) strong','Ауа райы архивін жүктеу'],['.agent-step:nth-child(2) small','Болжам уақытына сай оқу деректері'],['.agent-step:nth-child(3) strong','28 күндік болжамды қайта есептеу'],['.agent-step:nth-child(3) small','Әр күнге арналған ECMWF IFS болжамы'],['.agent-step:nth-child(4) strong','Талдау және экспорт'],['.agent-step:nth-child(4) small','Сапаны тексеру · CSV · аудит журналы'],['#progressLabel','ДЕРЕК ЖҮКТЕЛГЕН СОҢ ДАЙЫН'],['#chart-panel .eyebrow','АҚПАНДАҒЫ ТЕСТ КЕЗЕҢІ'],['.chart-panel h2','Сағаттық қуат болжамы'],['.chart-legend:nth-child(1)','1-турбина'],['.chart-legend:nth-child(2)','2-турбина'],['#downloadLink','↓ CSV жүктеу'],['#chartEmpty strong','Әзірге болжам жоқ'],['#chartEmpty p','Ақпан айын есептеу үшін турбиналардың өлшенген деректерін жүктеңіз.'],['.chart-y-label','НОРМАЛАНҒАН БЕЛСЕНДІ ҚУАТ'],['.chart-x-label','<span>1 АҚПАН</span><span>7 АҚПАН</span><span>14 АҚПАН</span><span>21 АҚПАН</span><span>28 АҚПАН</span>'],['.chart-foot span:first-child','<i class="foot-dot"></i> Болжам мәндері 0–1 аралығында нормаланған'],['#metricSummary','Дәлдік өлшемдері ақпан айының нақты деректері берілгенде шығады'],
      ['.detail-card:nth-child(1) .eyebrow','01 · БОЛЖАМ ЦИКЛІ'],['.detail-card:nth-child(1) h2','Күн сайынғы 48 сағат'],['.detail-card:nth-child(1) p','Әр есептеу 00:00-де басталғандай орындалады. Агент тек сол уақытта жарияланып үлгерген ECMWF IFS архивтік болжамын таңдап, келесі 48 сағатты есептейді.'],['.detail-card:nth-child(1) .detail-points','<span>24 сағаттық нәтиже</span><span>1–28 ақпан 2026</span><span>Алматы уақыты</span>'],['.detail-card:nth-child(2) .eyebrow','02 · ДЕРЕК ЖӘНЕ МОДЕЛЬ'],['.detail-card:nth-child(2) h2','Әр турбинаға жеке модель'],['.detail-card:nth-child(2) p','Тарихи өндіріс жел жылдамдығы, оның қуат қисығы түрлендірулері және алдыңғы сағаттардың қуаты арқылы үйретіледі. Екі турбинаға екі бөлек Ridge регрессиясы құрылады.'],['.detail-card:nth-child(2) .detail-points','<span>Жел · 100 м</span><span>Температура · 2 м</span><span>Нәтиже · 0–1</span>'],['.detail-card:nth-child(3) .eyebrow','03 · ТЕКСЕРУ ЖӘНЕ НӘТИЖЕ'],['.detail-card:nth-child(3) h2','Қайта тексеруге болатын есеп'],['.detail-card:nth-child(3) p','Жүктеген файлдағы уақыт, бос мәндер мен шектер тексеріледі. Болжам CSV файлында, ал кезеңдер мен сапа тексерістері есеп пен аудит журналында сақталады.'],['#reportLink','Есепті ашу ↗'],['#traceLink','Аудит журналын ашу ↗'],['footer span:first-child','WINDCAST АГЕНТІ <b>·</b> ТЕКСЕРІЛЕТІН ЖЕЛ ЭНЕРГИЯСЫ БОЛЖАМЫ'],['footer span:last-child','ТЕК АРХИВТІК АУА РАЙЫ <b>·</b> КЕЙІНГІ НАҚТЫ ДЕРЕК ЖОҚ']
    ]
  }
};

L.ru = {
  ...L.kk, title:'WindCast — Панель прогнозов', pick:'Выбрать файл', upload:'Загрузить и рассчитать', retry:'Загрузить снова', loading:'Загрузка…', run:'Запустить агента', idle:'Загрузите исторические данные организатора, чтобы начать.', queued:'Файл принят. Запускается расчёт дневных прогнозов.', ingest:'Проверяется структура и диапазоны данных турбин.', weather:'Загружаются архивные данные о погоде.', replay:'Выполняется повторный расчёт дневных прогнозов.', complete:n=>`Расчёт завершён: готово почасовых прогнозов — ${n}.`, failed:'Неизвестная ошибка.', running:'ВЫПОЛНЯЕТСЯ', error:'ОШИБКА', ready:'ГОТОВО', waiting:'ОЖИДАНИЕ', stepReady:'ГОТОВО', attention:'Требуется внимание', dataWait:'Ожидание данных', statusRunning:'Выполняется', stage:{ingest:'ПРОВЕРКА ДАННЫХ',weather_history:'ЗАГРУЗКА ПОГОДЫ',replay:'ПЕРЕСЧЁТ ПРОГНОЗА',complete:'ЗАВЕРШЕНО',failed:'ОШИБКА'}, static:L.kk.static.map(([s])=>[s,'']),
};
L.en = {
  ...L.kk, title:'WindCast — Forecast Dashboard', pick:'Choose file', upload:'Upload and calculate', retry:'Upload again', loading:'Uploading…', run:'Run agent', idle:'Upload the organizer’s historical data to begin.', queued:'File received. Daily forecast replay is starting.', ingest:'Checking turbine data structure and value ranges.', weather:'Loading archived weather data.', replay:'Recalculating daily forecasts.', complete:n=>`Replay complete: ${n} hourly forecasts are ready.`, failed:'Unknown error.', running:'RUNNING', error:'ERROR', ready:'READY', waiting:'WAITING', stepReady:'DONE', attention:'Needs attention', dataWait:'Waiting for data', statusRunning:'Running', stage:{ingest:'VALIDATING DATA',weather_history:'LOADING WEATHER',replay:'REPLAYING FORECASTS',complete:'COMPLETE',failed:'ERROR'}, static:L.kk.static.map(([s])=>[s,'']),
};

const ruStatic = ['РАБОЧАЯ ОБЛАСТЬ','Панель прогноза','Запуски агента','Результаты','АРХИВНЫЙ ПОВТОР','BAITC · HACKALEM AI<br>ВЕТРОЭНЕРГЕТИКА / 2026','ОПЕРАЦИИ <span>/</span> ПРОГНОЗ','ECMWF IFS · АРХИВ','КАЗАХСТАН · ВЕТРОЭНЕРГЕТИКА','ЕЖЕДНЕВНЫЙ ПОВТОР · ФЕВРАЛЬ 2026','Прогноз <em>выработки ветра</em>','Почасовой прогноз для двух турбин у Балхаша. Каждый запуск использует архив погоды, доступный на тот момент.','Запустить агента','ПЕРИОД ПОВТОРА','28 <small>дней</small>','1–28 ФЕВРАЛЯ 2026','ГОРИЗОНТ ПРОГНОЗА','24–48 <small>ч</small>','ПОЧАСОВО · ПО ГОРИЗОНТУ','ТУРБИНЫ','02 <small>шт.</small>','43.6452° с. ш. · 78.5356° в. д.','СТАТУС АГЕНТА','ВХОДНЫЕ ДАННЫЕ','Загрузить историю турбин','ШАГ 01','Загрузите почасовые измерения организатора за март 2023 — январь 2026. Поддерживаются CSV, XLSX и XLSM.','Перетащите файл или <u>выберите</u>','UTF-8 CSV или Excel · до 80 МБ','Обязательные поля: время, ID турбины, скорость ветра, нормированная мощность и температура. <a href="/template_observations.csv" download>Шаблон CSV ↗</a>','Для проектного прогноза нужны исходные данные организатора.','АВТОНОМНЫЙ ПРОЦЕСС','Работа агента','Проверка данных турбин','Столбцы · диапазоны · время UTC','Загрузка архива погоды','Признаки обучения, согласованные с прогнозом','Повтор 28 дневных прогнозов','Архивный запуск ECMWF IFS для каждой даты','Анализ и экспорт','Контроль качества · CSV · журнал аудита','ГОТОВ ПОСЛЕ ЗАГРУЗКИ ДАННЫХ','ТЕСТОВЫЙ ПЕРИОД · ФЕВРАЛЬ','Почасовой прогноз мощности','Турбина 1','Турбина 2','↓ Экспорт CSV','Прогнозов пока нет','Загрузите историю измерений турбин для расчёта прогноза за февраль.','НОРМИРОВАННАЯ АКТИВНАЯ МОЩНОСТЬ','<span>1 ФЕВ</span><span>7 ФЕВ</span><span>14 ФЕВ</span><span>21 ФЕВ</span><span>28 ФЕВ</span>','<i class="foot-dot"></i> Прогноз нормирован в диапазоне 0–1','Оценка точности появится после загрузки фактических данных за февраль','01 · ЦИКЛ ПРОГНОЗА','Ежедневный горизонт 48 часов','Каждый цикл имитирует запуск в 00:00. Агент выбирает архив ECMWF IFS, уже доступный к этому времени, и прогнозирует следующие 48 часов.','<span>Результат за 24 часа</span><span>1–28 февраля 2026</span><span>Время Алматы</span>','02 · ДАННЫЕ И МОДЕЛЬ','Отдельная модель для каждой турбины','Модель обучается на выработке, скорости ветра, преобразованиях кривой мощности и предыдущей мощности. Для каждой турбины строится отдельная Ridge-регрессия.','<span>Ветер · 100 м</span><span>Температура · 2 м</span><span>Выход · 0–1</span>','03 · ПРОВЕРКА И РЕЗУЛЬТАТ','Проверяемый расчёт','Проверяются время, пропуски и диапазоны. Прогноз сохраняется в CSV, этапы расчёта и контроль качества — в отчёте и журнале аудита.','Открыть отчёт ↗','Открыть журнал аудита ↗','АГЕНТ WINDCAST <b>·</b> ПРОВЕРЯЕМЫЙ ПРОГНОЗ ВЕТРОЭНЕРГЕТИКИ','ТОЛЬКО АРХИВ ПОГОДЫ <b>·</b> БЕЗ БУДУЩИХ НАБЛЮДЕНИЙ'];
const enStatic = ['WORKSPACE','Forecast desk','Agent runs','Results','ARCHIVE REPLAY','BAITC · HACKALEM AI<br>WIND GENERATION / 2026','OPERATIONS <span>/</span> FORECAST DESK','ECMWF IFS · ARCHIVED','KAZAKHSTAN · WIND ENERGY','DAILY REPLAY · FEBRUARY 2026','Wind generation <em>forecast</em>','Hourly generation forecasts for two turbines near Balkhash. Each run uses weather data available at issue time.','Run agent','REPLAY WINDOW','28 <small>days</small>','FEB 01–28, 2026','FORECAST HORIZON','24–48 <small>h</small>','HOURLY · LEAD-TIME ALIGNED','TURBINES','02 <small>units</small>','43.6452° N · 78.5356° E','AGENT STATUS','INPUT DATA','Connect turbine history','STEP 01','Upload organizer measurements from March 2023 through January 2026. CSV, XLSX and XLSM are supported.','Drop a file or <u>browse</u>','UTF-8 CSV or Excel · max 80 MB','Required: timestamp, turbine ID, wind speed, normalized power and temperature. <a href="/template_observations.csv" download>CSV template ↗</a>','Organizer data is required for project-specific forecasts.','AUTONOMOUS WORKFLOW','Agent activity','Validate turbine data','Schema · ranges · UTC time','Load archived weather','Forecast-aligned training features','Replay 28 daily forecasts','Archived ECMWF IFS run for each issue','Analyze &amp; export','Quality checks · CSV · audit log','READY WHEN YOUR DATA IS','FEBRUARY TEST PERIOD','Hourly power forecast','Turbine 1','Turbine 2','↓ Export CSV','No forecasts yet','Upload measured turbine history to generate the February replay.','NORMALIZED ACTIVE POWER','<span>FEB 01</span><span>FEB 07</span><span>FEB 14</span><span>FEB 21</span><span>FEB 28</span>','<i class="foot-dot"></i> Forecast output is normalized to 0–1','Accuracy scores appear when February actuals are provided','01 · FORECAST CYCLE','Daily 48-hour horizon','Each cycle simulates a 00:00 issue time. The agent selects an archived ECMWF IFS forecast already available then and predicts the next 48 hours.','<span>24-hour output</span><span>Feb 1–28, 2026</span><span>Almaty time</span>','02 · DATA &amp; MODEL','A separate model for each turbine','The model learns from generation history, wind speed, power-curve transforms and previous-hour power. Each turbine has its own Ridge regression.','<span>Wind · 100 m</span><span>Temperature · 2 m</span><span>Output · 0–1</span>','03 · VALIDATION &amp; OUTPUT','Auditable forecast run','Timestamps, missing values and ranges are checked. Forecasts are saved as CSV; cycle details and quality checks are recorded in a report and audit log.','Open report ↗','Open audit log ↗','WINDCAST AGENT <b>·</b> AUDITABLE WIND POWER FORECASTING','ARCHIVED WEATHER ONLY <b>·</b> NO FUTURE OBSERVATIONS'];

L.ru = {
  ...L.kk, title:'WindCast — Панель прогнозов', pick:'Выбрать файл', upload:'Загрузить и рассчитать', retry:'Загрузить снова', loading:'Загрузка…', run:'Запустить агента', idle:'Загрузите исторические данные организатора, чтобы начать.', queued:'Файл принят. Запускается расчёт дневных прогнозов.', ingest:'Проверяется структура и диапазоны данных турбин.', weather:'Загружаются архивные данные о погоде.', replay:'Выполняется повторный расчёт дневных прогнозов.', complete:n=>`Расчёт завершён: готово почасовых прогнозов — ${n}.`, failed:'Неизвестная ошибка.', running:'ВЫПОЛНЯЕТСЯ', error:'ОШИБКА', ready:'ГОТОВО', waiting:'ОЖИДАНИЕ', stepReady:'ГОТОВО', attention:'Требуется внимание', dataWait:'Ожидание данных', statusRunning:'Выполняется', stage:{ingest:'ПРОВЕРКА ДАННЫХ',weather_history:'ЗАГРУЗКА ПОГОДЫ',replay:'ПЕРЕСЧЁТ ПРОГНОЗА',complete:'ЗАВЕРШЕНО',failed:'ОШИБКА'}, static:L.kk.static.map(([s])=>[s,'']),
  ...L.kk, title:'WindCast — Панель прогнозов', pick:'Выбрать файл', upload:'Загрузить и рассчитать', retry:'Загрузить снова', loading:'Загрузка…', run:'Запустить агента', idle:'Загрузите исторические данные организатора, чтобы начать.', queued:'Файл принят. Запускается расчёт дневных прогнозов.', ingest:'Проверяется структура и диапазоны данных турбин.', weather:'Загружаются архивные данные о погоде.', replay:'Выполняется повторный расчёт дневных прогнозов.', complete:n=>`Расчёт завершён: готово почасовых прогнозов — ${n}.`, failed:'Неизвестная ошибка.', running:'ВЫПОЛНЯЕТСЯ', error:'ОШИБКА', ready:'ГОТОВО', waiting:'ОЖИДАНИЕ', stepReady:'ГОТОВО', attention:'Требуется внимание', dataWait:'Ожидание данных', statusRunning:'Выполняется', stage:{ingest:'ПРОВЕРКА ДАННЫХ',weather_history:'ЗАГРУЗКА ПОГОДЫ',replay:'ПЕРЕСЧЁТ ПРОГНОЗА',complete:'ЗАВЕРШЕНО',failed:'ОШИБКА'}, static:L.kk.static.map(([s],i)=>[s,ruStatic[i]]),
};
L.en = {
  ...L.kk, title:'WindCast — Forecast Dashboard', pick:'Choose file', upload:'Upload and calculate', retry:'Upload again', loading:'Uploading…', run:'Run agent', idle:'Upload the organizer’s historical data to begin.', queued:'File received. Daily forecast replay is starting.', ingest:'Checking turbine data structure and value ranges.', weather:'Loading archived weather data.', replay:'Recalculating daily forecasts.', complete:n=>`Replay complete: ${n} hourly forecasts are ready.`, failed:'Unknown error.', running:'RUNNING', error:'ERROR', ready:'READY', waiting:'WAITING', stepReady:'DONE', attention:'Needs attention', dataWait:'Waiting for data', statusRunning:'Running', stage:{ingest:'VALIDATING DATA',weather_history:'LOADING WEATHER',replay:'REPLAYING FORECASTS',complete:'COMPLETE',failed:'ERROR'}, static:L.kk.static.map(([s])=>[s,'']),
  ...L.kk, title:'WindCast — Forecast Dashboard', pick:'Choose file', upload:'Upload and calculate', retry:'Upload again', loading:'Uploading…', run:'Run agent', idle:'Upload the organizer’s historical data to begin.', queued:'File received. Daily forecast replay is starting.', ingest:'Checking turbine data structure and value ranges.', weather:'Loading archived weather data.', replay:'Recalculating daily forecasts.', complete:n=>`Replay complete: ${n} hourly forecasts are ready.`, failed:'Unknown error.', running:'RUNNING', error:'ERROR', ready:'READY', waiting:'WAITING', stepReady:'DONE', attention:'Needs attention', dataWait:'Waiting for data', statusRunning:'Running', stage:{ingest:'VALIDATING DATA',weather_history:'LOADING WEATHER',replay:'REPLAYING FORECASTS',complete:'COMPLETE',failed:'ERROR'}, static:L.kk.static.map(([s],i)=>[s,enStatic[i]]),
};

function tr(key, ...args) {
  const value = L[currentLang]?.[key] ?? L.kk[key] ?? '';
  return typeof value === 'function' ? value(...args) : value;
}

function applyLanguage(lang) {
  currentLang = L[lang] ? lang : 'kk';
  localStorage.setItem('windcast-language', currentLang);
  document.documentElement.lang = currentLang;
  document.title = tr('title');
  L[currentLang].static.forEach(([selector, html]) => {
    const element = document.querySelector(selector);
    if (!element || html === undefined) return;
    if (selector === '.source-pill') element.innerHTML = `<span class="pulse"></span> ${html}`;
    else if (selector === '.api-indicator') element.innerHTML = `<i></i> ${html}`;
    else if (selector === '.nav-item.active') element.innerHTML = `<span class="nav-icon">◫</span> ${html}`;
    else if (selector === '.nav-item:nth-of-type(3)') element.innerHTML = `<span class="nav-icon">⌘</span> ${html} <span class="nav-count">01</span>`;
    else if (selector === '.nav-item:nth-of-type(4)') element.innerHTML = `<span class="nav-icon">▤</span> ${html}`;
    else if (selector === '.chart-legend:nth-child(1)') element.innerHTML = `<i class="legend-one"></i> ${html}`;
    else if (selector === '.chart-legend:nth-child(2)') element.innerHTML = `<i class="legend-two"></i> ${html}`;
    else element.innerHTML = html;
  });
  document.querySelectorAll('.lang-switch button').forEach(button => {
    const active = button.dataset.lang === currentLang;
    button.setAttribute('aria-pressed', String(active));
  });
  const credit = document.querySelector('.hero-caption a');
  credit.textContent = currentLang === 'ru' ? 'Фото: ветропарк Бадамша · Eni ↗' : currentLang === 'en' ? 'Photo: Badamsha Wind Farm · Eni ↗' : 'Фото: Бадамша жел паркі · Eni ↗';
  uploadButton.innerHTML = selectedFile ? `${tr('upload')} <span>→</span>` : `${tr('pick')} <span>↑</span>`;
  if (latestStatus) paintStatus(latestStatus);
}
document.querySelectorAll('.lang-switch button').forEach(button => button.addEventListener('click', () => applyLanguage(button.dataset.lang)));
applyLanguage(currentLang);
const ruStatic = ['РАБОЧАЯ ОБЛАСТЬ','Панель прогноза','Запуски агента','Результаты','АРХИВНЫЙ ПОВТОР','BAITC · HACKALEM AI<br>ВЕТРОЭНЕРГЕТИКА / 2026','ОПЕРАЦИИ <span>/</span> ПРОГНОЗ','ECMWF IFS · АРХИВ','КАЗАХСТАН · ВЕТРОЭНЕРГЕТИКА','ЕЖЕДНЕВНЫЙ ПОВТОР · ФЕВРАЛЬ 2026','Прогноз <em>выработки ветра</em>','Почасовой прогноз для двух турбин у Балхаша. Каждый запуск использует архив погоды, доступный на тот момент.','Запустить агента','ПЕРИОД ПОВТОРА','28 <small>дней</small>','1–28 ФЕВРАЛЯ 2026','ГОРИЗОНТ ПРОГНОЗА','24–48 <small>ч</small>','ПОЧАСОВО · ПО ГОРИЗОНТУ','ТУРБИНЫ','02 <small>шт.</small>','43.6452° с. ш. · 78.5356° в. д.','СТАТУС АГЕНТА','ВХОДНЫЕ ДАННЫЕ','Загрузить историю турбин','ШАГ 01','Загрузите почасовые измерения организатора за март 2023 — январь 2026. Поддерживаются CSV, XLSX и XLSM.','Перетащите файл или <u>выберите</u>','UTF-8 CSV или Excel · до 80 МБ','Обязательные поля: время, ID турбины, скорость ветра, нормированная мощность и температура. <a href="/template_observations.csv" download>Шаблон CSV ↗</a>','Для проектного прогноза нужны исходные данные организатора.','АВТОНОМНЫЙ ПРОЦЕСС','Работа агента','Проверка данных турбин','Столбцы · диапазоны · время UTC','Загрузка архива погоды','Признаки обучения, согласованные с прогнозом','Повтор 28 дневных прогнозов','Архивный запуск ECMWF IFS для каждой даты','Анализ и экспорт','Контроль качества · CSV · журнал аудита','ГОТОВ ПОСЛЕ ЗАГРУЗКИ ДАННЫХ','ТЕСТОВЫЙ ПЕРИОД · ФЕВРАЛЬ','Почасовой прогноз мощности','Турбина 1','Турбина 2','↓ Экспорт CSV','Прогнозов пока нет','Загрузите историю измерений турбин для расчёта прогноза за февраль.','НОРМИРОВАННАЯ АКТИВНАЯ МОЩНОСТЬ','<span>1 ФЕВ</span><span>7 ФЕВ</span><span>14 ФЕВ</span><span>21 ФЕВ</span><span>28 ФЕВ</span>','<i class="foot-dot"></i> Прогноз нормирован в диапазоне 0–1','Оценка точности появится после загрузки фактических данных за февраль','01 · ЦИКЛ ПРОГНОЗА','Ежедневный горизонт 48 часов','Каждый цикл имитирует запуск в 00:00. Агент выбирает архив ECMWF IFS, уже доступный к этому времени, и прогнозирует следующие 48 часов.','<span>Результат за 24 часа</span><span>1–28 февраля 2026</span><span>Время Алматы</span>','02 · ДАННЫЕ И МОДЕЛЬ','Отдельная модель для каждой турбины','Модель обучается на выработке, скорости ветра, преобразованиях кривой мощности и предыдущей мощности. Для каждой турбины строится отдельная Ridge-регрессия.','<span>Ветер · 100 м</span><span>Температура · 2 м</span><span>Выход · 0–1</span>','03 · ПРОВЕРКА И РЕЗУЛЬТАТ','Проверяемый расчёт','Проверяются время, пропуски и диапазоны. Прогноз сохраняется в CSV, этапы расчёта и контроль качества — в отчёте и журнале аудита.','Открыть отчёт ↗','Открыть журнал аудита ↗','АГЕНТ WINDCAST <b>·</b> ПРОВЕРЯЕМЫЙ ПРОГНОЗ ВЕТРОЭНЕРГЕТИКИ','ТОЛЬКО АРХИВ ПОГОДЫ <b>·</b> БЕЗ БУДУЩИХ НАБЛЮДЕНИЙ'];

 uploadButton.disabled = false;
  uploadButton.innerHTML = 'Жүктеу және есептеу <span>→</span>';
  document.querySelector('#uploadHint').textContent = 'Файл дайын. Жүктеп, болжамды бастауға болады.';
  uploadButton.innerHTML = `${tr('upload')} <span>→</span>`;
  document.querySelector('#uploadHint').textContent = tr('fileReady');
  uploadError.hidden = true;
  uploadButton.disabled = true;
  uploadButton.textContent = 'Жүктелуде…';
  uploadButton.textContent = tr('loading');
  uploadError.hidden = true;
    if (!response.ok) throw new Error(payload.error || 'Файлды жүктеу сәтсіз аяқталды');
    agentMessage.textContent = 'Файл қабылданды. Агент деректерді тексеріп, ауа райы архивін жүктеп, есептеуді бастайды.';
    agentMessage.textContent = tr('queued');
  } catch (error) {
  } finally {
    if (selectedFile) uploadButton.innerHTML = 'Қайта жүктеу <span>↻</span>';
    if (selectedFile) uploadButton.innerHTML = `${tr('retry')} <span>↻</span>`;
  }
  if (runButton.dataset.hasInput !== 'true') {
    document.querySelector('#uploadHint').textContent = 'Алдымен тарихи CSV немесе Excel файлын жүктеңіз.';
    document.querySelector('#uploadHint').textContent = tr('needFile');
    document.querySelector('#upload-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.querySelector('#dropzone').scrollIntoView({ behavior: 'smooth', block: 'center' });
    agentMessage.textContent = 'Болжамды бастау үшін ұйымдастырушының турбина тарихы керек. Төмендегі батырманы басып файл таңдаңыз.';
    agentMessage.textContent = tr('idle');
    return;
function paintStatus(s) {
  latestStatus = s;
  const running = Boolean(s.running);
  const failed = s.stage === 'failed';
  const stageNames = { ingest: 'ДЕРЕКТІ ТЕКСЕРУ', weather_history: 'АУА РАЙЫН ЖҮКТЕУ', replay: 'БОЛЖАМДЫ ҚАЙТА ЕСЕПТЕУ', complete: 'АЯҚТАЛДЫ', failed: 'ҚАТЕ' };
  statusValue.innerHTML = `<span class="status-dot ${running ? 'running' : failed ? 'error' : s.stage === 'complete' ? 'ok' : 'idle'}"></span>${running ? 'Орындалуда' : failed ? 'Назар аудару қажет' : s.stage === 'complete' ? 'Дайын' : s.input_file ? 'Дайын' : 'Дерек күтілуде'}`;
  statusFoot.textContent = running ? `${stageNames[s.stage] || 'АГЕНТ'} · ${s.percent || 0}%` : failed ? 'ДЕРЕКТІ / ЖЕЛІНІ ТЕКСЕРІҢІЗ' : s.stage === 'complete' ? '28 КҮН ЕСЕПТЕЛДІ · ФАЙЛ ДАЙЫН' : s.input_file ? 'ДЕРЕК ЖҮКТЕЛДІ · ІСКЕ ҚОСУҒА ДАЙЫН' : 'БАСТАУ ҮШІН ДЕРЕК ЖҮКТЕҢІЗ';
  const T = L[currentLang];
  const stageNames = T.stage;
  statusValue.innerHTML = `<span class="status-dot ${running ? 'running' : failed ? 'error' : s.stage === 'complete' ? 'ok' : 'idle'}"></span>${running ? T.statusRunning : failed ? T.attention : s.stage === 'complete' || s.input_file ? T.ready : T.dataWait}`;
  statusFoot.textContent = running ? `${stageNames[s.stage] || 'AGENT'} · ${s.percent || 0}%` : failed ? T.check : s.stage === 'complete' ? T.cyclesDone : s.input_file ? T.fileLoaded : T.uploadToStart;
  runButton.disabled = running;
  uploadButton.disabled = running;
  if (!selectedFile && !running) uploadButton.innerHTML = 'Файлды таңдау <span>↑</span>';
  if (!selectedFile && !running) uploadButton.innerHTML = `${tr('pick')} <span>↑</span>`;
  document.querySelector('#progressBar').style.width = `${Math.min(100, s.percent || 0)}%`;
  document.querySelector('#progressPercent').textContent = `${Math.min(100, s.percent || 0)}%`;
  document.querySelector('#progressLabel').textContent = running ? (s.cycle ? `${s.cycle}-КҮН ЕСЕПТЕЛУДЕ` : (stageNames[s.stage] || 'ОРЫНДАЛУДА')) : failed ? 'АГЕНТ ҚАТЕМЕН ТОҚТАДЫ' : s.stage === 'complete' ? 'ҚАЙТА ЕСЕПТЕУ АЯҚТАЛДЫ' : 'ДЕРЕК ЖҮКТЕЛГЕН СОҢ ДАЙЫН';
  document.querySelector('#progressLabel').textContent = running ? (s.cycle ? T.cycle(s.cycle) : (stageNames[s.stage] || T.running)) : failed ? T.stopped : s.stage === 'complete' ? T.finished : T.readyWhenUploaded;
  const messages = {
    idle: 'Бастау үшін ұйымдастырушының тарих файлын жүктеңіз.',
    queued: 'Файл қабылданды. Күнделікті болжамдарды есептеу басталады.',
    ingest: 'Турбина деректерінің құрылымы мен мәндері тексерілуде.',
    weather_history: 'Архивтік ауа райы деректері жүктелуде.',
    replay: s.cycle ? `${s.cycle} күніне арналған болжам есептелуде.` : 'Күнделікті болжамдар қайта есептелуде.',
    complete: `Қайта есептеу аяқталды: ${s.report?.forecast_rows || 0} сағаттық нәтиже дайын.`,
    idle: T.idle, queued: T.queued, ingest: T.ingest, weather_history: T.weather,
    replay: s.cycle ? T.replayDay(s.cycle) : T.replay,
    complete: T.complete(s.report?.forecast_rows || 0),
  };
  agentMessage.textContent = s.stage === 'failed' ? (s.message || 'Белгісіз қате.') : (messages[s.stage] || 'Агент әзірге әрекет жасаған жоқ.');
  document.querySelector('#agentBadge').textContent = running ? '● ОРЫНДАЛУДА' : failed ? '● ҚАТЕ' : s.stage === 'complete' ? '● ДАЙЫН' : '● КҮТУДЕ';
  agentMessage.textContent = s.stage === 'failed' ? (s.message || T.failed) : (messages[s.stage] || T.idle);
  document.querySelector('#agentBadge').textContent = running ? `● ${T.running}` : failed ? `● ${T.error}` : s.stage === 'complete' ? `● ${T.ready}` : `● ${T.waiting}`;
  document.querySelector('#agentBadge').style.color = running ? '#5b843f' : failed ? '#b95049' : '';
    el.classList.toggle('done', s.stage === 'complete' || (!failed && (index < stageIndex || (s.stage === 'replay' && index < 2))));
    el.querySelector('.step-state').textContent = el.classList.contains('done') ? 'ДАЙЫН' : el.classList.contains('active') ? 'ОРЫНДАЛУДА' : failed && index === Math.max(0, stageIndex) ? 'ҚАТЕ' : 'КҮТУДЕ';
    el.querySelector('.step-state').textContent = el.classList.contains('done') ? T.stepReady : el.classList.contains('active') ? T.running : failed && index === Math.max(0, stageIndex) ? T.error : T.waiting;
  });
  document.querySelector('#traceLink').classList.remove('disabled');
  document.querySelector('#metricSummary').textContent = report.metrics ? 'Бағалау көрсеткіштері ақпанның нақты деректері бойынша есептелді' : 'Дәлдік өлшемдері ақпан айының нақты деректері берілгенде шығады';
  document.querySelector('#metricSummary').textContent = report.metrics ? tr('metricsReady') : tr('metricsPending');

  
