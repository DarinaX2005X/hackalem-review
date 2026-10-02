import {test} from 'node:test';
import assert from 'node:assert/strict';
import {renderReviewView,splitParagraphs,demoStatusLink} from '../web/review-view.js';

test('Live demo links use one label regardless of verification status',()=>{
 for(const label of ['Работает','Недоступно','Указано','Не проверено']){
  const html=demoStatusLink(label,'https://example.com/demo');
  assert.match(html,/>Ссылка ↗<\/a>/);
  assert.doesNotMatch(html,new RegExp(label));
 }
 assert.equal(demoStatusLink('Работает',null),'Не найдено');
 assert.equal(demoStatusLink('Указано','javascript:alert(1)'),'Не найдено');
});

test('Late submission has zero without claiming a code review or runtime tests',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 renderReviewView(target,{status:'late_submission',score:0,judges:[],expectedJudges:0,
   reason:'Разбор кода не проводился: первый коммит с решением после дедлайна.',
   repoUrl:'https://github.com/BAITC-Hacks/hack-fixture',firstSolutionCommit:'a'.repeat(40)});
 assert.match(target.innerHTML,/<strong>0<\/strong>/);
 assert.match(target.innerHTML,/Разбор не проводился/);
 assert.match(target.innerHTML,/Дисквалификация/);
 assert.match(target.innerHTML,/после дедлайна/);
 assert.doesNotMatch(target.innerHTML,/Запуск подтверждён|Баллы по критериям|GPT-5.6 Luna|Отчёт неполный/);
});

test('No commits is shown as disqualification with its own reason',()=>{
 const target={isConnected:true,innerHTML:''};
 renderReviewView(target,{status:'no_commits',score:0});
 assert.match(target.innerHTML,/Дисквалификация/);
 assert.match(target.innerHTML,/Нет коммитов/);
 assert.match(target.innerHTML,/13:00–18:00/);
 assert.doesNotMatch(target.innerHTML,/Первый коммит с решением ↗/);
});

test('Long Russian text is split at sentence boundaries without changing evidence',()=>{
 const text='В main.py:27 используется https://api.x.ai/v1 с таймаутом 0.8 секунды. '+
   'Основной сценарий проверен на предоставленных тестовых данных. '.repeat(18);
 const parts=splitParagraphs(text);
 assert.ok(parts.length>1);
 assert.equal(parts.join(' '),text.trim());
 assert.ok(parts[0].includes('https://api.x.ai/v1'));
 assert.ok(parts[0].includes('0.8'));
 assert.deepEqual(splitParagraphs('Первый абзац.\n\nВторой абзац.'),['Первый абзац.','Второй абзац.']);
});

test('Two-judge roster accepts both Luna models and labels one pending',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 const report={methodVersion:4,expectedJudges:2,status:'partial',score:null,snapshot:'abc',judges:[judge('GPT-6 Luna')]};
 renderReviewView(target,report);
 assert.match(target.innerHTML,/Готово 1 из 2 судей/);
 renderReviewView(target,{...report,status:'complete',score:81,judges:[...report.judges,judge('GPT-5.6 Luna')]});
 assert.match(target.innerHTML,/Судей: 2/);
 assert.equal((target.innerHTML.match(/role="tabpanel"/g)||[]).length,2);
});

const criterion={name:'Результат',score:18,max:20,awarded:'Рабочий сценарий',deductions:'Не проверен крайний случай',evidence:['src/app.py:12 показан обработчик']};
const judge=model=>({model,judgeScore:81,overallSummary:'Решение соответствует основному сценарию.',global:{criteria:[criterion],total:81},case:{criteria:[criterion],total:81},caseRequirements:[{requirement:'Обработать тестовый вход',status:'met',explanation:'Проверено на данных.',evidence:['src/app.py:12']}],testData:{provided:['sample.csv'],used:['sample.csv'],checks:[{input:'sample.csv',method:'Запуск в Docker',result:'Выход создан',conclusion:'Основной путь работает'}],limitations:[]},runtime:{status:'working',build:'Собран',start:'Стартовал',scenario:'Прошёл',environment:'Docker',summary:'Проверено.',checks:[{command:'docker run app',result:'exit 0'}],limitations:[]},liveDemo:{status:'none',url:null,notes:'Ссылки нет.'},fiveHourContext:'Для пяти часов выбран разумный объём.',strengths:['Работает'],gaps:['Мало тестов'],futureAdvice:[{principle:'Проверять риск первым',why:'Экономит время',how:'Сделать короткий вертикальный сценарий'}],uncertainties:[]});

test('One complete Luna review has a final score without a second judge or average',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 renderReviewView(target,{methodVersion:4,expectedJudges:1,status:'complete',score:81,snapshot:'abc',judges:[judge('GPT-5.6 Luna')]});
 assert.match(target.innerHTML,/Проверка GPT-5.6 Luna/);
 assert.match(target.innerHTML,/Запуск подтверждён/);
 assert.match(target.innerHTML,/class="judge-tabs" hidden/);
 assert.doesNotMatch(target.innerHTML,/GPT-6 Luna|Среднее арифметическое|Итог ещё не рассчитан|Выберите судью/);
});

test('A single published judge is readable without a final average',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 renderReviewView(target,{methodVersion:4,status:'partial',score:null,snapshot:'abc',judges:[judge('GPT-6 Luna')]});
 assert.match(target.innerHTML,/Готово 1 из 3 судей/);
 assert.match(target.innerHTML,/Итог ещё не рассчитан/);
 assert.match(target.innerHTML,/Требования кейса/);
 assert.equal((target.innerHTML.match(/role="tabpanel"/g)||[]).length,1);
 assert.doesNotMatch(target.innerHTML,/Среднее арифметическое|NaN|Все судьи запустили/);
});

test('Detailed review is scanable, escaped, and uses Live демо wording',()=>{
  const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
  renderReviewView(target,{repoId:'hack-test',repoUrl:'https://github.com/BAITC-Hacks/actual-repository',snapshot:'1234567890123456789012345678901234567890',score:81,judges:[judge('GPT-6 Sol'),judge('GPT-6 Luna')]});
  assert.match(target.innerHTML,/Требования кейса/);
  assert.match(target.innerHTML,/Проверка на данных кейса/);
  assert.match(target.innerHTML,/Что взять в следующий хакатон/);
  assert.match(target.innerHTML,/Live демо/);
  assert.doesNotMatch(target.innerHTML,/Лив-демо|\[object Object\]/);
  assert.match(target.innerHTML,/role="tablist"/);
  assert.match(target.innerHTML,/Баллы по критериям/);
  assert.match(target.innerHTML,/Критерии хакатона/);
  assert.match(target.innerHTML,/blob\/1234567890123456789012345678901234567890\/src\/app.py#L12/);
  assert.match(target.innerHTML,/github\.com\/BAITC-Hacks\/actual-repository\/blob/);
});

test('A started app with a blocked external scenario is still counted as started',()=>{
  const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
  const sol=judge('GPT-6 Sol'),luna=judge('GPT-6 Luna');
  sol.runtime.status='partial';luna.runtime.status='partial';
  renderReviewView(target,{repoId:'hack-test',repoUrl:'https://github.com/BAITC-Hacks/actual-repository',snapshot:'1234567890123456789012345678901234567890',score:81,judges:[sol,luna]});
  assert.match(target.innerHTML,/Все судьи запустили/);
  assert.match(target.innerHTML,/Основной сценарий/);
  assert.match(target.innerHTML,/Проверен частично/);
});

test('Evidence-based advice and limitations are shown without changing old reports',()=>{
  const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
  const sol=judge('GPT-6 Sol'),luna=judge('GPT-6 Luna');
  sol.findings=[{id:'F1',kind:'defect',verification:'source',claim:'Принят отрицательный бюджет',expected:'Отклонить вход',actual:'Число прошло в расчёт',evidence:['src/app.py:12']},{id:'L1',kind:'limitation',verification:'unverified',claim:'Ключ отсутствовал у проверяющего',expected:'Ответ API',actual:'Вызов не выполнялся',evidence:['Конфигурация проверки']}];
  sol.futureAdvice=[{principle:'Проверить ограничения до интерфейса',why:'Отрицательный бюджет прошёл в расчёт.',how:'Взять допустимый и два граничных входа из будущего кейса.',findingIds:['F1'],successCheck:'Недопустимые входы отвергнуты.',timeboxMinutes:15}];
  sol.global={criteria:[{...criterion,deductionItems:[{points:2,findingId:'F1',reason:'Нарушено ограничение бюджета'}]}],total:81};
  renderReviewView(target,{repoId:'hack-test',repoUrl:'https://github.com/BAITC-Hacks/actual-repository',snapshot:'1234567890123456789012345678901234567890',score:81,judges:[sol,luna]});
  assert.match(target.innerHTML,/Факты и границы проверки/);
  assert.match(target.innerHTML,/Не является основанием для снятия баллов/);
  assert.match(target.innerHTML,/Как понять, что получилось/);
  assert.match(target.innerHTML,/F1: −2/);
  assert.match(target.innerHTML,/15 мин/);
});


test('Three independent judges have separate panels and all score columns',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 const names=['Qwen3.8-Flash','LongCat 2.5 Preview','MiMo-V2.6-Flash'];
 renderReviewView(target,{methodVersion:4,repoId:'hack-test',repoUrl:'https://github.com/org/repo',snapshot:'abc',score:81,judges:names.map(judge)});
 for(const name of names)assert.ok(target.innerHTML.includes(name));
 assert.equal((target.innerHTML.match(/role="tabpanel"/g)||[]).length,3);
 const ids=[...target.innerHTML.matchAll(/id="(judge-[^"]+)"/g)].map(m=>m[1]);
 assert.equal(new Set(ids).size,3);
 assert.match(target.innerHTML,/Судей: 3/);
});


test('Detailed awards have individual headings, sources and score rationale',()=>{
 const target={isConnected:true,innerHTML:'',querySelectorAll:()=>[]};
 const judges=['Qwen3.8-Flash','LongCat 2.5 Preview','MiMo-V2.6-Flash'].map(judge);
 judges[0].global=structuredClone(judges[0].global);
 judges[0].global.criteria[0].awardedDetails=[{aspect:'Проверка ограничения бюджета',implementation:'Сумма считается по каждой строке.',value:'Пользователь видит объяснимый результат.',verification:'source',evidence:['src/plan.py:18']}];
 judges[0].global.criteria[0].scoreReasoning='Основной путь реализован, крайний случай подтверждён как дефект.';
 renderReviewView(target,{methodVersion:4,repoId:'hack-test',repoUrl:'https://github.com/BAITC-Hacks/test',snapshot:'abc',score:81,judges});
 assert.match(target.innerHTML,/<h6>Проверка ограничения бюджета<\/h6>/);
 assert.match(target.innerHTML,/Почему 18 из 20/);
 assert.match(target.innerHTML,/Вывод по исходникам/);
 assert.match(target.innerHTML,/src\/plan.py#L18/);
});
