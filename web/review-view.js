const judgeKey = judge => judge.model.toLowerCase().replace(/[^a-z0-9]+/g,'-');
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const number=value=>Number(value).toLocaleString('ru-RU',{maximumFractionDigits:2});
export function splitParagraphs(value){
  const blocks=String(value??'').split(/\n\s*\n|\r?\n/).map(s=>s.trim()).filter(Boolean);
  return blocks.flatMap(block=>{
    if(block.length<=550)return [block];
    const sentences=typeof Intl.Segmenter==='function'?[...new Intl.Segmenter('ru',{granularity:'sentence'}).segment(block)].map(s=>s.segment):[block];
    const result=[];let current='';
    for(const sentence of sentences){
      if(current.length>=280&&current.length+sentence.length>550){result.push(current.trim());current='';}
      current+=sentence;
    }
    if(current.trim())result.push(current.trim());
    return result;
  });
}
const prose=value=>`<div class="review-prose">${splitParagraphs(value).map(p=>`<p>${esc(p)}</p>`).join('')}</div>`;
const list=(items,empty='Не указано')=>items?.length?`<ul class="review-list">${items.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>`:`<p class="small">${empty}</p>`;
const requirementLabel={met:'Выполнено',partial:'Частично',missing:'Не выполнено',unverified:'Не проверено'};
const runtimeLabel={working:'Сценарий работает',partial:'Приложение запущено',failed:'Не запущено',blocked:'Старт не проверен'};

export function demoStatusLink(label,url){
  try{
    const parsed=new URL(url);
    if(['https:','http:'].includes(parsed.protocol))return `<a class="demo-status-link" href="${esc(parsed.href)}" target="_blank" rel="noopener noreferrer">Ссылка ↗</a>`;
  }catch{}
  return 'Не найдено';
}

function sourceLink(value,report){
  const match=/^([^\r\n:]+):([0-9]+)(?:\b|\s)/.exec(value);
  if(!match)return esc(value);
  const path=match[1].replaceAll('\\','/');
  if(path.startsWith('/')||path.includes('..')||!report.snapshot||!/^https:\/\/github\.com\/BAITC-Hacks\/[A-Za-z0-9._-]+$/.test(report.repoUrl||''))return esc(value);
  const url=`${report.repoUrl}/blob/${encodeURIComponent(report.snapshot)}/${path.split('/').map(encodeURIComponent).join('/')}#L${match[2]}`;
  return `<a href="${url}" target="_blank" rel="noopener noreferrer">${esc(value)} ↗</a>`;
}

function scoreScale(scale,title,report){
  if(!scale)return `<section class="review-block"><h4>${esc(title)}</h4><p>У этого кейса нет отдельной опубликованной шкалы с баллами. Судья применил общие критерии.</p></section>`;
  return `<section class="review-block"><div class="review-block-head"><h4>${esc(title)}</h4><strong>${number(scale.total)} / 100</strong></div><div class="score-rows">${scale.criteria.map(item=>`<details class="score-row"><summary><span class="score-name">${esc(item.name)}</span><span class="score-track" aria-hidden="true"><i style="width:${Math.max(0,Math.min(100,item.score/item.max*100))}%"></i></span><strong>${number(item.score)} / ${number(item.max)}</strong><span class="criterion-toggle"><span class="criterion-show">Показать разбор</span><span class="criterion-hide">Скрыть разбор</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></span></summary><div class="score-explanation"><div><h5>За что начислены баллы</h5>${prose(item.awarded)}${item.awardedDetails?.length?`<div class="awarded-details">${item.awardedDetails.map(point=>`<article><h6>${esc(point.aspect)}</h6>${prose(point.implementation)}<p><b>Почему это ценно:</b> ${esc(point.value)}</p><p class="small">${point.verification==='observed'?'Подтверждено выполнением':'Вывод по исходникам'}</p><div class="source-inline">${point.evidence.map(e=>`<span>${sourceLink(e,report)}</span>`).join('')}</div></article>`).join('')}</div>`:''}${item.scoreReasoning?`<div class="score-reasoning"><h6>Почему ${number(item.score)} из ${number(item.max)}</h6>${prose(item.scoreReasoning)}</div>`:''}</div><div><h5>За что сняты баллы</h5>${prose(item.deductions)}${item.deductionItems?.length?list(item.deductionItems.map(d=>(String(d.findingId)+': −'+number(d.points)+' балла — '+d.reason))):String()}</div>${item.evidence?.length?`<div class="source-list"><h5>Где это видно</h5><ul>${item.evidence.map(e=>`<li>${sourceLink(e,report)}</li>`).join('')}</ul></div>`:''}</div></details>`).join('')}</div></section>`;
}

function requirements(judge,report){return `<section class="review-block" id="requirements-${judgeKey(judge)}"><div class="review-block-head"><h4>Требования кейса</h4><span class="review-count">${judge.caseRequirements.length} проверено</span></div><div class="requirement-list">${judge.caseRequirements.map(item=>`<article class="requirement-row"><span class="status-pill ${esc(item.status)}">${requirementLabel[item.status]||'Не проверено'}</span><div><h5>${esc(item.requirement)}</h5>${prose(item.explanation)}${item.evidence?.length?`<div class="source-inline">${item.evidence.map(e=>`<span>${sourceLink(e,report)}</span>`).join('')}</div>`:''}</div></article>`).join('')}</div></section>`;}

function testData(judge){const info=judge.testData;return `<section class="review-block"><div class="review-block-head"><h4>Проверка на данных кейса</h4><span class="review-count">${info.checks.length} проверок</span></div><div class="dataset-source"><div><span>Предоставлено</span>${list(info.provided,'Файлы не указаны')}</div><div><span>Использовано</span>${list(info.used,'Использование не подтверждено')}</div></div>${info.checks.length?`<div class="dataset-checks">${info.checks.map((check,index)=>`<article><span class="check-number">${index+1}</span><div><h5>${esc(check.input)}</h5><p><b>Как проверяли:</b> ${esc(check.method)}</p><p><b>Результат:</b> ${esc(check.result)}</p><p class="check-conclusion">${esc(check.conclusion)}</p></div></article>`).join('')}</div>`:'<p>Судья не смог провести проверку на приложенных данных.</p>'}${info.limitations?.length?`<details class="review-detail"><summary>Ограничения проверки</summary>${list(info.limitations)}</details>`:''}</section>`;}

function runtime(judge){const item=judge.runtime;return `<section class="review-block"><div class="review-block-head"><h4>Локальная проверка</h4><span class="status-pill ${esc(item.status)}">${runtimeLabel[item.status]||'Не проверено'}</span></div>${prose(item.summary)}<div class="runtime-steps"><div><span>Сборка</span><p>${esc(item.build)}</p></div><div><span>Старт</span><p>${esc(item.start)}</p></div><div><span>Сценарий</span><p>${esc(item.scenario)}</p></div></div><p class="small">Окружение: ${esc(item.environment)}</p>${item.checks?.length?`<details class="review-detail"><summary>Команды и результаты</summary><ol class="run-checks">${item.checks.map(check=>`<li><code>${esc(check.command)}</code><span>${esc(check.result)}</span></li>`).join('')}</ol></details>`:''}${item.limitations?.length?`<details class="review-detail"><summary>Что мешало полной проверке</summary>${list(item.limitations)}</details>`:''}</section>`;}

function demo(judge){const item=judge.liveDemo;return `<section class="review-block"><div class="review-block-head"><h4>Live демо</h4><span class="status-pill">${demoStatusLink('',item.url)}</span></div><p>${esc(item.notes)}</p></section>`;}

function comparisonRows(judges, scale){
  const first=judges.find(j=>j[scale])?.[scale];
  if(!first)return '';
  return first.criteria.map((item,index)=>`<tr><th scope="row">${esc(item.name)} <span>из ${number(item.max)}</span></th>${judges.map(j=>`<td>${j[scale]?.criteria[index]?number(j[scale].criteria[index].score):'—'}</td>`).join('')}</tr>`).join('');
}
function scoreComparison(judges){
  const table=scale=>`<div class="table-scroll"><table><thead><tr><th>Критерий</th>${judges.map(j=>`<th>${esc(j.model)}</th>`).join('')}</tr></thead><tbody>${comparisonRows(judges,scale)}</tbody></table></div>`;
  return `<section class="score-comparison" id="review-compare"><div><h2>Баллы по критериям</h2><p>${judges.length===1?'Оценка одного судьи':`${judges.length} независимых оценки`} по каждому критерию. Ниже доступны причины и подтверждения каждого балла.</p></div><div class="comparison-grid"><div><h3>Критерии хакатона</h3>${table('global')}</div>${judges.some(j=>j.case)?`<div><h3>Критерии кейса</h3>${table('case')}</div>`:''}</div></section>`;
}

function findings(judge,report){
  if(!judge.findings?.length)return '';
  const kind={defect:'Недостаток',strength:'Сильная сторона',limitation:'Ограничение проверки'};
  const basis={observed:'Проверено запуском',source:'Установлено по коду',unverified:'Не подтверждено'};
  return `<section class="review-block"><h4>Факты и границы проверки</h4><div class="requirement-list">${judge.findings.map(item=>`<article class="requirement-row"><span class="status-pill">${esc(item.id)} · ${esc(kind[item.kind])}</span><div><h5>${esc(item.claim)}</h5><p class="small">${esc(basis[item.verification])}</p><p><b>Ожидалось:</b> ${esc(item.expected)}</p><p><b>Фактически:</b> ${esc(item.actual)}</p>${item.kind==='limitation'?'<p class="small">Не является основанием для снятия баллов.</p>':''}<div class="source-inline">${item.evidence.map(value=>`<span>${sourceLink(value,report)}</span>`).join('')}</div></div></article>`).join('')}</div></section>`;
}

function advice(judge){if(!judge.futureAdvice?.length)return '';return `<section class="review-block"><h4>Что взять в следующий хакатон</h4><p class="small">Советы о подходе к будущим задачам, а не список правок уже сданного решения.</p><div class="advice-grid">${judge.futureAdvice.map((item,index)=>`<article><span>${index+1}</span><h5>${esc(item.principle)}</h5>${item.findingIds?.length?`<p><b>Основание:</b> ${item.findingIds.map(id=>esc(judge.findings?.find(f=>f.id===id)?.claim||id)).join('; ')}</p>`:''}<p>${esc(item.why)}</p><p><b>Как применить:</b> ${esc(item.how)}</p>${item.successCheck?`<p><b>Как понять, что получилось:</b> ${esc(item.successCheck)}</p><p class="small">Ориентир по времени: ${number(item.timeboxMinutes)} мин.</p>`:''}</article>`).join('')}</div></section>`;}

function judgePanel(judge,report,index){const slug=judgeKey(judge);return `<div id="judge-${slug}" class="judge-panel" role="tabpanel" aria-labelledby="tab-${slug}" ${index>0?'hidden':''}><div class="judge-intro">${prose(judge.overallSummary)}<div class="judge-score"><strong>${number(judge.judgeScore)}</strong><span>балл судьи</span></div></div>${judge.editorialNote?`<p class="editorial-note">${esc(judge.editorialNote)}</p>`:''}<div class="judge-quick"><div><h4>Сильные стороны</h4>${list(judge.strengths)}</div><div><h4>Что снизило оценку</h4>${list(judge.gaps)}</div></div><p class="five-hour"><b>С учётом пяти часов:</b> ${esc(judge.fiveHourContext)}</p>${scoreScale(judge.global,'Критерии хакатона',report)}${scoreScale(judge.case,'Критерии кейса',report)}${findings(judge,report)}${requirements(judge,report)}${testData(judge)}${runtime(judge)}${demo(judge)}${advice(judge)}${judge.uncertainties?.length?`<details class="review-detail"><summary>Что судья не смог установить</summary>${list(judge.uncertainties)}</details>`:''}</div>`;}

export function renderReviewView(target,report){
  if(!target?.isConnected)return;
  if(['late_submission','no_commits'].includes(report.status)){
    const commitLink=/^https:\/\/github\.com\/BAITC-Hacks\/[A-Za-z0-9._-]+$/.test(report.repoUrl||'')&&/^[a-f0-9]{40}$/.test(report.firstSolutionCommit||'')
      ?`<a href="${esc(report.repoUrl+'/commit/'+report.firstSolutionCommit)}" target="_blank" rel="noopener noreferrer">Первый коммит с решением ↗</a>`:'';
    const reason=report.reason||(report.status==='late_submission'?'Первое решение после дедлайна 18:00.':'Нет коммитов в период хакатона: 13:00–18:00 по Астане.');
    target.innerHTML=`<section class="review-result disqualification"><div><span class="disqualified-badge">Дисквалификация</span><h2>${report.status==='late_submission'?'Решение после 18:00':'Нет коммитов в период хакатона'}</h2>${prose(reason)}<p>Разбор не проводился. Проект не участвует в топ-5 и резерве. Статус относится к этому неофициальному разбору.</p>${commitLink}</div><div class="result-number"><strong>0</strong><span>дисквалификация</span></div></section>`;
    return;
  }
  const judges=report.judges||[];
  const expected=report.expectedJudges??(report.methodVersion>=4?3:2);
  const partial=report.status==='partial'&&judges.length>0&&judges.length<expected&&report.score==null;
  if(!partial&&judges.length !== expected){target.textContent='Отчёт неполный. Повторите загрузку позднее.';return;}
  const run=judges.map(j=>j.runtime.status);
  const demos=judges.map(j=>j.liveDemo.status);
  const started=run.map(x=>x==='working'||x==='partial');
  const runText=started.every(Boolean)?(partial||judges.length===1?'Запуск подтверждён':'Все судьи запустили'):started.some(Boolean)?`Запустили ${started.filter(Boolean).length} из ${judges.length}`:'Старт не подтверждён';
  const scenarioText=run.every(x=>x==='working')?(judges.length===1?'Подтверждён':'Все подтвердили'):run.includes('working')?`Подтвердили ${run.filter(x=>x==='working').length} из ${judges.length}`:run.includes('partial')?'Проверен частично':'Не подтверждён';
  const demoText=demos.includes('confirmed')?'Работает':demos.includes('unreachable')?'Недоступно':demos.includes('claimed')?'Ссылка указана':'Не найдено';
  target.innerHTML=`<section class="review-result" id="review-overview"><div><h2>Независимый разбор</h2><p>${partial?`Готово ${judges.length} из ${expected} судей. Остальные оценки ещё не готовы. Итоговое среднее и место в рейтинге появятся после всех проверок.`:judges.length===1?`Проверка ${esc(judges[0].model)} по критериям хакатона и кейса.`:`Судей: ${judges.length}. Проверен один срез кода. Среднее арифметическое их оценок.`} Результат неофициальный.</p><div class="review-scores">${judges.map(j=>`<span>${esc(j.model)} <strong>${number(j.judgeScore)}</strong></span>`).join('')}</div></div><div class="result-number"><strong>${partial?'—':number(report.score)}</strong><span>${partial?'Итог ещё не рассчитан':'из 100'}</span></div></section><div class="review-facts"><div><span>Проверенная версия</span><strong>${esc(report.snapshot.slice(0,12))}</strong></div><div><span>Приложение</span><strong>${esc(runText)}</strong></div><div><span>Основной сценарий</span><strong>${esc(scenarioText)}</strong></div><div><span>Live демо</span><strong>${demoStatusLink(demoText,judges.find(j=>j.liveDemo?.url)?.liveDemo.url)}</strong></div><div><span>Данные кейса</span><strong>${judges.map(j=>j.testData.checks.length).join(' / ')} проверок</strong></div></div><nav class="review-jumps" aria-label="Разделы отчёта"><button type="button" data-review-jump="review-overview">Итог</button><button type="button" data-review-jump="review-compare">Баллы</button><button type="button" data-review-jump="review-judges">Подробный разбор</button><button type="button" data-review-jump="full-readme">README</button></nav>${scoreComparison(judges)}<section id="review-judges" class="review-judges"><div class="review-section-head"><div><h2>Подробный отчёт</h2><p> В каждой строке балла раскрывается обоснование и источник.</p></div></div><div class="judge-tabs" ${judges.length===1?'hidden':''} role="tablist" aria-label="ИИ-судьи">${judges.map((j,i)=>`<button id="tab-${judgeKey(j)}" type="button" role="tab" aria-controls="judge-${judgeKey(j)}" aria-selected="${i===0}" data-judge-tab="${judgeKey(j)}">${esc(j.model)} <strong>${number(j.judgeScore)}</strong></button>`).join('')}</div>${judges.map((j,i)=>judgePanel(j,report,i)).join('')}</section>`;
  target.querySelectorAll('[data-judge-tab]').forEach(button=>button.addEventListener('click',()=>{const active=button.dataset.judgeTab;target.querySelectorAll('[data-judge-tab]').forEach(tab=>tab.setAttribute('aria-selected',String(tab.dataset.judgeTab===active)));target.querySelectorAll('.judge-panel').forEach(panel=>panel.hidden=panel.id!==`judge-${active}`);}));
  target.querySelectorAll('[data-review-jump]').forEach(button=>button.addEventListener('click',()=>document.getElementById(button.dataset.reviewJump)?.scrollIntoView({behavior:'smooth',block:'start'})));
  target.querySelectorAll('.judge-tabs [role="tab"]').forEach((button,index,tabs)=>button.addEventListener('keydown',event=>{if(event.key!=='ArrowRight'&&event.key!=='ArrowLeft')return;event.preventDefault();tabs[(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length].click();tabs[(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length].focus();}));
}
