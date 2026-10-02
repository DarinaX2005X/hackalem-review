import {renderReviewView,demoStatusLink} from './review-view.js';
import {rankingMarks,disqualified} from './ranking.js';
import {renderPaginationControls} from './pagination.js';
const main=document.querySelector('#main');
const nav=document.querySelector('#navigation');
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>new Intl.NumberFormat('ru-RU').format(n);
const icons={search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',back:'<path d="M19 12H5m5-5-5 5 5 5"/>',external:'<path d="M14 4h6v6m0-6-10 10"/><path d="M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/>',check:'<path d="m5 12 4 4L19 6"/>',file:'<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8Z"/><path d="M14 3v5h5M8 12h8m-8 4h6"/>',download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v4h16v-4"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',close:'<path d="m6 6 12 12M6 18 18 6"/>',copy:'<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M15 8V4H4v11h4"/>',users:'<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 4v2"/>'};
const icon=(name)=>`<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name]||icons.file}</svg>`;
let data,route='catalog',params=new URLSearchParams(),pageSize=30,backTo='#catalog';
const scrollPositions=new Map();
let pendingScroll=null;
history.scrollRestoration='manual';
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#"]');
  if(!link)return;
  const current=location.hash||'#catalog',next=link.getAttribute('href');
  scrollPositions.set(current,window.scrollY);
  pendingScroll=route==='catalog'&&next.startsWith('#catalog')?window.scrollY:(next.startsWith('#catalog')||next==='#cases'?scrollPositions.get(next)??0:0);
});
const caseById=id=>data.cases.find(c=>c.id===Number(id));
const caseTitle=p=>caseById(p.caseId)?.title||'Кейс уточняется';
const safeHref=url=>/^https:\/\/(?:github\.com|raw\.githubusercontent\.com)\//.test(url||'')?escape(url):'#';
const labelReadme=p=>p.readmeStatus==='found'?(p.readmeTemplate?'Шаблон':'Есть README'):(p.readmeStatus==='missing'?'Не найден':'Не проверен');
const readmePill=p=>`<span class="pill ${p.readmeStatus!=='found'||p.readmeTemplate?'neutral':''}">${icon(p.readmeStatus==='found'?'check':'file')}${labelReadme(p)}</span>`;
const markdown=window.markdownit({html:false,linkify:true,typographer:false});
const defaultLinkOpen=markdown.renderer.rules.link_open||((tokens,index,options,env,self)=>self.renderToken(tokens,index,options));
markdown.renderer.rules.link_open=(tokens,index,options,env,self)=>{tokens[index].attrSet('target','_blank');tokens[index].attrSet('rel','noopener noreferrer');return defaultLinkOpen(tokens,index,options,env,self);};
function readmeHtml(source,p){
  const tokens=markdown.parse(source,{});
  const base=p.readmeUrl?.slice(0,p.readmeUrl.lastIndexOf('/')+1);
  const walk=list=>{for(const token of list){if(token.children)walk(token.children);for(const attr of ['href','src']){const value=token.attrGet?.(attr);if(!value||!base||/^(?:[a-z]+:|\/\/|#)/i.test(value))continue;try{const url=new URL(value,base);if(url.protocol==='https:')token.attrSet(attr,url.href);}catch{}}}};
  walk(tokens);
  return markdown.renderer.render(tokens,markdown.options,{});
}
async function loadReadme(p){
  const target=document.querySelector('#full-readme');if(!target)return;
  try{const response=await fetch('./data/readmes/'+encodeURIComponent(p.id)+'.md');if(!response.ok)throw Error(String(response.status));const source=await response.text();if(target.isConnected)target.innerHTML=readmeHtml(source,p);}
  catch{if(target.isConnected)target.textContent='Полный README не загрузился. Откройте исходный файл на GitHub по ссылке выше.';}
}
function teamPanel(p){
  const anonymous=(p.anonymousMembers||[]).map(name=>`<span class="member-name">${escape(name)}</span>`).join('');
  const linked=(p.members||[]).map(name=>`<a href="https://github.com/${encodeURIComponent(name)}" target="_blank" rel="noopener noreferrer">${escape(name)} ↗</a>`).join('');
  const overflow=p.contributorsCount>3;
  const people=overflow?anonymous:linked||anonymous;
  const count=p.teamSize===null?'Состав не удалось установить':`${p.teamSize} ${p.teamSize===1?'участник':p.teamSize===2?'участника':'участника'}`;
  return `<section class="panel"><h2>Участники команды</h2><p class="team-count">${count}</p>${people?`<div class="members">${people}</div>`:''}<p class="small">${escape(p.teamSizeNote||'По публичному списку GitHub Contributors. ИИ и боты исключены.')}</p>${overflow?`<details><summary class="toggle-details">Все аккаунты GitHub Contributors (${p.contributorsCount})</summary><div class="members">${linked}</div></details>`:''}${p.excludedBots?.length?`<details><summary class="toggle-details">Исключённые ИИ и боты: ${p.excludedBots.length}</summary><p class="small">${p.excludedBots.map(escape).join(', ')}</p></details>`:''}<p class="small">Коммиты всех зарегистрированных участников в период хакатона ещё не подтверждены.</p></section>`;
}
let reviewIndex={reviews:[]},reviewFingerprint='',reviewRefreshTimer;
const reviewedCount=caseId=>data.projects.filter(p=>(caseId==null||p.caseId===Number(caseId))&&Number.isFinite(reviewById(p.id)?.score)).length;
const reviewById=id=>{
  const row=reviewIndex.reviews.find(row=>row.repoId===id)||(reviewIndex.partialReviews||[]).find(row=>row.repoId===id);
  const decision=reviewIndex.eligibility?.[id];
  return decision?{...row,...decision,repoId:id,score:0}:row;
};
const eligibleReviews=()=>reviewIndex.reviews.map(row=>reviewById(row.repoId)).filter(row=>!disqualified(row));
const disqualificationLabel=row=>row?.status==='late_submission'?'Решение после 18:00':'Нет коммитов в 13:00–18:00';
const dqBadge=row=>disqualified(row)?`<span class="disqualified-badge">Дисквалификация</span><span class="dq-reason">${disqualificationLabel(row)}</span>`:'';
const scoredInCase=id=>eligibleReviews().filter(row=>row.caseId===Number(id)).sort((a,b)=>b.score-a.score||a.repoId.localeCompare(b.repoId));
const hasLiveDemo=row=>(row.liveDemos||[]).some(d=>{try{return ['http:','https:'].includes(new URL(d.url).protocol);}catch{return false;}});
const scoreText=value=>value==null?'—':Number(value).toLocaleString('ru-RU',{maximumFractionDigits:2});
function reviewState(row,kind){
  if(kind==='demo')return row&&hasLiveDemo(row)?'Ссылка':'Не найдено';
  if(!row)return 'Не проверено';
  if(disqualified(row))return kind==='run'?'Разбор не проводился':'Не проверено';
  const values=row.runStatuses;
  if(kind==='run')return values.every(x=>x==='working'||x==='partial')?'Запущено':values.some(x=>x==='working'||x==='partial')?'Запущено одним судьёй':values.every(x=>x==='failed')?'Не запущено':'Не проверено';
  return 'Не проверено';
}
function topFive(caseId){return rankingMarks(eligibleReviews(),caseId);}
const topBadge=mark=>mark?.kind==='reserve'?'<span class="reserve-badge" title="Баллы равны баллу пятой команды">Резерв · балл как у 5-й</span>':mark?`<span class="top-five-badge" aria-label="Топ-5, место ${mark.rank}"><span>${mark.rank}</span>Топ-5</span>`:'';
const rankClass=mark=>mark?.kind==='top'?'top-five-row':mark?.kind==='reserve'?'reserve-row':'';
function leaderboard(caseId){
  const c=caseById(caseId),rows=scoredInCase(caseId),marks=topFive(caseId),evaluated=reviewedCount(caseId),complete=evaluated===c.count;
  if(!rows.length)return `<section class="review-pending"><h2>Рейтинг ожидает судейство</h2><p>${evaluated?`Оценено ${evaluated} из ${c.count} проектов. Пока все итоговые оценки — 0 за дисквалификацию.`:'Ни одна команда этого кейса ещё не получила оценку.'}</p></section>`;
  let rank=0,last=null;
  return `<section class="panel"><h2>${complete?'Топ-10 кейса':'Предварительный топ-10'}</h2><p class="small">С оценкой ${evaluated} из ${c.count} проектов. ${complete?'Выделены первые пять проектов по баллу.':'Выделены первые пять среди уже оценённых. Список изменится по мере новых проверок.'} Резерв — команды вне первых пяти с баллом пятой команды. Оценка неофициальная.</p><div class="table-scroll"><table class="stats-table leaderboard"><thead><tr><th>Место</th><th>Команда</th><th>Оценка / 100</th></tr></thead><tbody>${rows.filter((r,i)=>i<10||marks.get(r.repoId)?.kind==='reserve').map((r,i)=>{if(last!==r.score){rank=i+1;last=r.score;}const p=data.projects.find(p=>p.id===r.repoId);return `<tr class="${rankClass(marks.get(r.repoId))}"><td>${i<5?`<span class="rank-number">${rank}</span>`:rank}</td><td>${topBadge(marks.get(r.repoId))}<a href="#project/${escape(r.repoId)}">${escape(p?.name||r.repoId)}</a></td><td><strong>${scoreText(r.score)}</strong></td></tr>`}).join('')}</tbody></table></div></section>`;
}
function partialReviewsPanel(){
 const rows=reviewIndex.partialReviews||[];if(!rows.length)return '';
 return `<section class="panel"><h2>Первые отчёты судей</h2><p class="small">Остальные оценки ещё не готовы. Эти проекты пока не участвуют в рейтинге; итоговое среднее не рассчитано.</p><div class="table-scroll"><table class="stats-table"><thead><tr><th>Команда</th><th>Готово судей</th><th>Оценки</th></tr></thead><tbody>${rows.map(r=>`<tr><td><a href="#project/${escape(r.repoId)}">${escape(data.projects.find(p=>p.id===r.repoId)?.name||r.repoId)}</a></td><td>${r.judgeScores.length} из ${r.expectedJudges}</td><td>${r.judgeScores.map(j=>`${escape(j.model)}: ${scoreText(j.score)} / 100`).join('; ')}</td></tr>`).join('')}</tbody></table></div></section>`;
}
function homeOverview(){
  if(!reviewedCount())return '';
  const reviewed=reviewedCount();
  const started=reviewIndex.reviews.filter(row=>row.runStatuses.some(status=>status==='working'||status==='partial')).length;
  const demos=reviewIndex.reviews.filter(hasLiveDemo).length;
  return `<div class="home-overview"><div><strong>${reviewed} / ${data.projects.length}</strong><span>проектов оценено</span></div><div><strong>${started}</strong><span>удалось запустить</span></div><div><strong>${demos}</strong><span>проектов со ссылкой на Live демо</span></div></div>`;
}
async function loadReview(p){
  const target=document.querySelector('#review-detail');if(!target)return;
  if(disqualified(reviewById(p.id))&&reviewById(p.id).status!=='late_submission'){renderReviewView(target,{...reviewById(p.id),repoUrl:p.url});return;}
  try{const response=await fetch('./data/reviews/'+(reviewById(p.id)?.status==='partial'?'partial/':'')+encodeURIComponent(p.id)+'.json');if(!response.ok)throw Error(String(response.status));const report=await response.json();renderReviewView(target,report);}
  catch{if(target.isConnected)target.textContent='Отчёт не загрузился. Обновите страницу и повторите попытку.';}
}
const caseHref=id=>'#catalog?case='+id;
function toast(text){const el=document.querySelector('#toast');el.textContent=text;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),2600);}
function navigate(hash){if(location.hash===hash)renderRoute();else location.hash=hash;}
function updateParam(key,value){value?params.set(key,value):params.delete(key);params.delete('page');history.replaceState(null,'','#catalog'+(params.size?'?'+params:''));renderCatalogResults();}
function filtered(){
  const q=(params.get('q')||'').trim().toLocaleLowerCase('ru');
  return data.projects.filter(p=>{
    if(q&&![p.name,p.id,p.product,...(p.members||[])].join(' ').toLocaleLowerCase('ru').includes(q))return false;
    const c=params.get('case');if(c&&(c==='unknown'?p.caseId!==null:p.caseId!==Number(c)))return false;
    const l=params.get('language');if(l&&(p.language||'Не указан')!==l)return false;
    const r=params.get('readme');if(r==='yes'&&(p.readmeStatus!=='found'||p.readmeTemplate))return false;if(r==='no'&&p.readmeStatus==='found')return false;if(r==='template'&&!p.readmeTemplate)return false;
    const s=params.get('size');if(s&&(s==='unknown'?(p.teamSize!==null&&p.teamSize<=3):p.teamSize!==Number(s)))return false;
    return true;
  }).sort((a,b)=>{
    const order=params.get('sort');
    if(order==='name'||order==='name-desc')return (order==='name-desc'?-1:1)*a.name.localeCompare(b.name,'ru',{numeric:true})||a.id.localeCompare(b.id);
    const first=reviewById(a.id)?.score,second=reviewById(b.id)?.score;
    // Unreviewed projects stay after scored projects in either direction.
    if(first==null||second==null)return (first==null)-(second==null)||a.id.localeCompare(b.id);
    return (order==='score-asc'?first-second:second-first)||a.id.localeCompare(b.id);
  });
}
function select(name,label,options){return `<div class="filter-control"><label for="filter-${name}">${label}</label><select id="filter-${name}" data-filter="${name}" aria-label="${label}">${options.map(([value,text])=>`<option value="${escape(value)}" ${params.get(name)===String(value)?'selected':''}>${escape(text)}</option>`).join('')}</select></div>`;}
function renderCatalog(){
  main.innerHTML=`<section class="hero"><div><h1>Все проекты HackAlem.<br>В одном месте.</h1><p>Найдите свою команду, изучите кейс и следите за независимым разбором решений.</p></div><div class="hero-aside"><div><strong class="hero-number">${fmt(data.projects.length)}</strong><span class="hero-label">проектов в каталоге</span></div><div><strong class="hero-number">12</strong><span class="hero-label">кейсов хакатона</span></div></div></section><p class="intro-note">${icon('info')}<span>${reviewedCount()?`Оценено проектов: ${reviewedCount()}. ${reviewedCount()<data.projects.length?'Проверки остальных проектов продолжаются.':'Все проекты получили итоговую оценку.'}`:'Оценки GPT-5.6 Luna появятся после проверки проектов.'} <a href="#method">Как устроен разбор</a></span></p>${homeOverview()}<div class="search-bar">${icon('search')}<input id="search" type="search" aria-label="Найти команду, проект или участника" placeholder="Название команды, проекта или GitHub участника" autocomplete="off" value="${escape(params.get('q')||'')}"><span class="key-hint">Ctrl K</span><button class="clear-search" id="clear-search" aria-label="Очистить поиск" ${params.get('q')?'':'hidden'}>${icon('close')}</button></div><div class="catalog-grid"><aside class="sidebar" aria-label="Кейсы"><p class="sidebar-label">Выберите кейс</p><div id="case-links"></div><p class="sidebar-info">Это независимый разбор.<br>Официальные результаты объявляют организаторы.<br><a href="#method">Источники и ограничения</a></p></aside><section class="results-panel" aria-label="Найденные проекты" id="results"></section></div>`;
  const input=document.querySelector('#search');input.addEventListener('input',()=>{updateParam('q',input.value);document.querySelector('#clear-search').hidden=!input.value;});
  document.querySelector('#clear-search').addEventListener('click',()=>{input.value='';updateParam('q','');document.querySelector('#clear-search').hidden=true;input.focus();});
  renderCatalogResults();
}
function renderCatalogResults(){
  const rows=filtered();const selected=params.get('case');const c=caseById(selected);
  // Top-5 and reserve badges describe a case ranking only. The all-projects
  // catalog has no single comparable ranking, so it stays visually neutral.
  const leaders=c?topFive(c.id):new Map();
  const pages=Math.max(1,Math.ceil(rows.length/pageSize));const page=Math.min(pages,Math.max(1,Math.trunc(Number(params.get('page')))||1));
  document.querySelector('#case-links').innerHTML=[['','Все проекты',data.projects.length],...data.cases.map(c=>[c.id,c.title,c.count]),...(data.coverage.unresolved?[['unknown','Кейс уточняется',data.coverage.unresolved]]:[])].map(([id,title,count])=>`<a href="${id?caseHref(id):'#catalog'}" class="case-link ${String(id)===(selected||'')?'active':''}" ${String(id)===(selected||'')?'aria-current="true"':''}><span>${escape(title)}${caseById(id)?`<small class="case-subtitle">${escape(caseById(id).subtitle)}</small>`:''}</span><span class="count">${fmt(count)}</span></a>`).join('');
  document.querySelector('#results').innerHTML=`<div class="results-head"><div><h2>${c?escape(c.title):selected==='unknown'?'Кейс уточняется':'Все проекты'}</h2><p aria-live="polite">${fmt(rows.length)} найдено${c?', '+escape(c.subtitle):''}</p></div><button class="text-button" id="export">${icon('download')}Скачать список</button></div><div class="filters"><div class="mobile-case">${select('case','Кейс',[['','Все кейсы'],...data.cases.map(c=>[c.id,c.title])])}</div>${select('language','Язык',[['','Любой язык'],...[...new Set(data.projects.map(p=>p.language||'Не указан'))].sort().map(x=>[x,x])])}${select('readme','README',[['','Любой README'],['yes','Не шаблон'],['template','Только шаблон'],['no','README не найден']])}${select('size','Команда',[['','Любой состав'],['1','1 участник'],['2','2 участника'],['3','3 участника'],['unknown','Состав уточняется']])}${select('sort','Порядок',[['','Сначала высокий балл'],['score-asc','Сначала низкий балл'],['name','Название: А–Я'],['name-desc','Название: Я–А']])}${params.size?'<button class="text-button" id="reset">Сбросить</button>':''}</div>${rows.length?`<table class="project-table"><thead><tr><th scope="col">Команда и проект</th><th scope="col">Кейс</th><th scope="col">Оценка</th><th scope="col" class="status-col">Запуск</th><th scope="col" class="status-col">Live демо</th><th><span class="sr-only">Открыть</span></th></tr></thead><tbody>${rows.slice((page-1)*pageSize,page*pageSize).map(p=>`<tr class="${disqualified(reviewById(p.id))?'disqualified-row':rankClass(leaders.get(p.id))}"><td>${topBadge(leaders.get(p.id))}${dqBadge(reviewById(p.id))}<a class="team-link" href="#project/${escape(p.id)}">${escape(p.name)}</a><span class="product-sub">${escape(p.product||p.id)}</span></td><td><a class="case-cell" href="${p.caseId?caseHref(p.caseId):'#catalog?case=unknown'}">${escape(caseTitle(p))}</a><span class="case-owner">${escape(caseById(p.caseId)?.subtitle||'')}</span></td><td class="score-col">${reviewById(p.id)?`<strong>${scoreText(reviewById(p.id).score)}</strong><small>из 100</small>`:'<span class="small">Пока нет</span>'}</td><td class="status-col">${escape(reviewState(reviewById(p.id),'run'))}</td><td class="status-col">${demoStatusLink(reviewState(reviewById(p.id),'demo'),reviewById(p.id)?.liveDemos?.find(d=>d.url)?.url)}</td><td><a href="#project/${escape(p.id)}" class="open-project" aria-label="Открыть проект ${escape(p.name)}">${icon('arrow')}</a></td></tr>`).join('')}</tbody></table><div class="pagination"><span>Показаны ${(page-1)*pageSize+1}…${Math.min(page*pageSize,rows.length)} из ${fmt(rows.length)}</span>${renderPaginationControls(page,pages)}</div>`:`<div class="empty">${icon('search')}<h3>Совпадений нет</h3><p>Попробуйте часть названия команды или уберите один из фильтров.</p><button class="button quiet" id="empty-reset">Показать все проекты</button></div>`}`;
  document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('change',()=>updateParam(el.dataset.filter,el.value)));
  document.querySelectorAll('[data-page]').forEach(el=>el.addEventListener('click',()=>{params.set('page',el.dataset.page);history.replaceState(null,'','#catalog?'+params);renderCatalogResults();document.querySelector('#results').scrollIntoView({block:'start'});}));
  for(const id of ['reset','empty-reset'])document.getElementById(id)?.addEventListener('click',()=>navigate('#catalog'));
  document.querySelector('#export').addEventListener('click',()=>exportCsv(rows));
  document.querySelectorAll('a[href^="#project/"]').forEach(el=>el.addEventListener('click',()=>backTo=location.hash));
}
function exportCsv(rows){
  const cell=value=>'"'+String(value??'').replace(/^[=+@-]/,"'$&").replace(/"/g,'""')+'"';
  const matrix=[['Команда','Проект','Категория','Кейс','Заказчик','GitHub','Основной язык','README','Участников','Подписи или аккаунты авторов','Примечание о составе','Итоговая оценка','Допуск','Запуск','Live демо'],...rows.map(p=>[p.name,p.product,caseTitle(p),caseById(p.caseId)?.subtitle,caseById(p.caseId)?.owner,p.url,p.language,labelReadme(p),p.teamSize,(p.members?.length?p.members:p.anonymousMembers||[]).join(', '),p.teamSizeNote||'',reviewById(p.id)?.score,disqualified(reviewById(p.id))?'Дисквалификация: '+disqualificationLabel(reviewById(p.id)):'',reviewState(reviewById(p.id),'run'),reviewState(reviewById(p.id),'demo')])];
  const blob=new Blob(['\ufeff'+matrix.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='hackalem-projects.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Список проектов сохранён');
}
function renderCases(){
  main.innerHTML=`<section class="hero"><div><h1>12 задач.<br>Разные подходы к решению.</h1><p>Выберите кейс, чтобы посмотреть команды, их проекты и исходное задание.</p></div><a class="button secondary" href="#catalog">Все проекты ${icon('arrow')}</a></section><div class="case-cards">${data.cases.map(c=>`<a class="case-card" href="#case/${c.id}"><h2>${escape(c.title)}</h2><span class="owner">${escape(c.subtitle)}</span><span class="case-company">${escape(c.owner)}</span><p>${escape(c.task.split('\n').filter(x=>x.trim().length>90)[0]||c.topic).slice(0,190)}</p><div class="case-bottom"><div><strong>${fmt(c.count)}</strong><span>проектов</span></div><div class="case-arrow">${icon('arrow')}</div></div></a>`).join('')}</div>${data.coverage.unresolved?`<p class="source-note">У ${data.coverage.unresolved} проектов кейс ещё уточняется. Они остаются в <a href="#catalog?case=unknown">общем каталоге</a>.</p>`:''}`;
}
function renderCase(id){
 const c=caseById(id);if(!c)return notFound();
 const rows=data.projects.filter(p=>p.caseId===c.id);const found=rows.filter(p=>p.readmeStatus==='found'&&!p.readmeTemplate).length;
 const paragraphs=c.task.split('\n').map(x=>x.trim()).filter(Boolean);const description=paragraphs.filter(x=>x.length>100);
 main.innerHTML=`<a class="back" href="#cases">${icon('back')}Все кейсы</a><section class="project-hero"><div><h1>${escape(c.title)}</h1><p class="subtitle">${escape(c.subtitle)}<br><span class="small">${escape(c.owner)}</span></p></div><a class="button" href="${caseHref(c.id)}">Все ${rows.length} проектов ${icon('arrow')}</a></section><div class="detail-grid"><section class="panel"><h2>Задача кейса</h2>${description.map(t=>`<p>${escape(t)}</p>`).join('')}<p class="small">Источник: предоставленный текст задания кейса ${c.id}.</p></section><section class="panel"><h2>Проверка кейса</h2><dl class="info-list"><div><dt>Команд</dt><dd>${rows.length}</dd></div><div><dt>README не шаблон</dt><dd>${found}</dd></div><div><dt>С оценкой</dt><dd>${reviewedCount(c.id)}</dd></div><div><dt>Удалось запустить</dt><dd>${scoredInCase(c.id).filter(r=>r.runStatuses.some(status=>status==='working'||status==='partial')).length}</dd></div><div><dt>Со ссылкой на Live демо</dt><dd>${scoredInCase(c.id).filter(hasLiveDemo).length}</dd></div></dl></section></div><div class="case-leaderboard">${leaderboard(c.id)}</div><a class="text-button" href="${caseHref(c.id)}">Перейти к полному списку команд ${icon('arrow')}</a>`;
}
function renderProject(id){
 const p=data.projects.find(p=>p.id===id);if(!p)return notFound();const c=caseById(p.caseId);
 main.innerHTML=`<a class="back" href="${escape(backTo)}">${icon('back')}Вернуться к проектам</a><section class="project-hero"><div><h1>${escape(p.name)}</h1>${p.product?`<p class="subtitle">${escape(p.product)}</p>`:''}</div><div class="project-actions"><a class="button" href="${safeHref(p.url)}" target="_blank" rel="noopener noreferrer">Открыть GitHub ${icon('external')}</a><button class="button secondary" id="share">${icon('copy')}Скопировать ссылку</button></div></section><div class="detail-grid"><div><section class="panel"><h2>О проекте</h2>${p.summary?`<p>${escape(p.summary)}</p><p class="small">Описание из README команды.</p>`:'<p>В доступном README нет содержательного описания проекта.</p>'}<dl class="info-list"><div><dt>Кейс</dt><dd>${c?`<a href="#case/${c.id}">${escape(c.title)}<span class="case-owner">${escape(c.subtitle)}</span></a>`:'Кейс уточняется'}</dd></div>${c?`<div><dt>Заказчик</dt><dd>${escape(c.owner)}</dd></div>`:''}<div><dt>Основной язык</dt><dd>${escape(p.language||'Не указан GitHub')}</dd></div><div><dt>README</dt><dd>${p.readmeUrl?`<a href="${safeHref(p.readmeUrl)}" target="_blank" rel="noopener noreferrer">${labelReadme(p)} ↗</a>`:labelReadme(p)}</dd></div><div><dt>Основная ветка</dt><dd>${escape(p.defaultBranch)}</dd></div></dl></section><section class="panel"><h2>Технологии в README</h2>${p.technologies.length?`<div class="techs">${p.technologies.map(t=>`<span class="tech">${escape(t)}</span>`).join('')}</div><p class="small">Упоминания в документации. Фактическое использование и запуск будут проверены отдельно.</p>`:'<p>В README не найдены названия технологий из собираемого списка.</p>'}</section></div><div>${teamPanel(p)}<p class="source-note">Оценки и выводы этого разбора не являются решением официального жюри.</p></div></div><section id="review-detail" class="review-detail">${reviewById(p.id)?'Загружаем отчёты судей…':'<div class="review-pending"><div class="review-icon">'+icon('file')+'</div><h2>Подробный разбор ещё впереди</h2><p>GPT-5.6 Luna оценит решение по критериям хакатона и кейса. Будут проверены тестовые данные, запуск и результаты. Советы помогут подготовиться к будущим хакатонам.</p></div>'}</section><section class="panel readme-panel"><div class="readme-head"><div><h2>Полный README</h2><p class="small">Документация команды без сокращений.</p></div>${p.readmeUrl?`<a class="text-button" href="${safeHref(p.readmeUrl)}" target="_blank" rel="noopener noreferrer">Исходный файл ${icon('external')}</a>`:''}</div><div id="full-readme" class="readme-content" aria-live="polite">Загружаем README…</div></section>`;
 loadReadme(p);
 if(reviewById(p.id))loadReview(p);
 document.querySelector('#share').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);toast('Ссылка на проект скопирована');}catch{toast('Скопируйте адрес страницы из строки браузера');}});
}
function counts(items,key){const result={};for(const p of items){const v=p[key]??'Не получено';result[v]=(result[v]||0)+1;}return Object.entries(result).sort((a,b)=>b[1]-a[1]);}
function renderStats(){
 const projects=data.projects,found=projects.filter(p=>p.readmeStatus==='found'&&!p.readmeTemplate).length,known=projects.filter(p=>p.teamSize!==null);const tech={};for(const p of projects)for(const t of p.technologies)tech[t]=(tech[t]||0)+1;
 main.innerHTML=`<section class="hero"><div><h1>Хакатон в числах</h1><p>Состав кейсов, документация и технологии. Только данные, которые помогают понять, с кем и над чем работали участники.</p></div><button class="button secondary" id="export-all">${icon('download')}Скачать каталог</button></section><div class="stats-summary"><div class="stat"><strong>${fmt(projects.length)}</strong><span>проектов в каталоге</span></div><div class="stat"><strong>${fmt(found)}</strong><span>README не шаблон</span></div><div class="stat"><strong>${fmt(reviewedCount())}</strong><span>проектов оценено</span></div><div class="stat"><strong>${fmt(known.length)}</strong><span>с установленным размером команды</span></div></div><div class="stats-columns"><div><section class="panel"><h2>Проекты по кейсам</h2><table class="stats-table"><thead><tr><th>Кейс</th><th>Всего</th><th>README не шаблон</th><th>Оценено</th><th>Запуск</th><th>Live демо</th></tr></thead><tbody>${data.cases.map(c=>`<tr><td><a href="${caseHref(c.id)}">${escape(c.title)}</a></td><td>${c.count}</td><td>${projects.filter(p=>p.caseId===c.id&&p.readmeStatus==='found'&&!p.readmeTemplate).length}</td><td>${reviewedCount(c.id)}</td><td>${scoredInCase(c.id).filter(r=>r.runStatuses.some(status=>status==='working'||status==='partial')).length}</td><td>${scoredInCase(c.id).filter(hasLiveDemo).length}</td></tr>`).join('')}${data.coverage.unresolved?`<tr><td><a href="#catalog?case=unknown">Кейс уточняется</a></td><td>${data.coverage.unresolved}</td><td>${projects.filter(p=>p.caseId===null&&p.readmeStatus==='found').length}</td></tr>`:''}</tbody></table></section><section class="panel"><h2>Сколько человек в команде</h2><p class="small">ИИ и боты исключены. Размер команды установлен для ${known.length} проектов по GitHub Contributors и истории веток. В 22 проектах GitHub показывает больше трёх аккаунтов; размер команды указан как три по правилу хакатона, а список аккаунтов открыт на странице проекта.</p><table class="stats-table"><thead><tr><th>Кейс</th><th>1</th><th>2</th><th>3</th><th>Уточняется</th></tr></thead><tbody>${[[null,'Все команды'],...data.cases.map(c=>[c.id,c.title])].map(([id,title])=>{const rows=id?projects.filter(p=>p.caseId===id):projects;return `<tr><td>${escape(title)}</td>${[1,2,3,'unknown'].map(n=>`<td>${rows.filter(p=>n==='unknown'?p.teamSize===null||p.teamSize>3:p.teamSize===n).length}</td>`).join('')}</tr>`;}).join('')}</tbody></table><p class="small">Наличие коммитов от всех участников требует проверки истории за 23 сентября. Этот показатель пока не рассчитан.</p></section></div><div><section class="panel"><h2>Основные языки</h2><p class="small">Один основной язык на репозиторий, по данным GitHub.</p><table class="stats-table"><thead><tr><th>Язык</th><th>Проектов</th></tr></thead><tbody>${counts(projects,'language').map(([name,count])=>`<tr><td><a href="#catalog?language=${encodeURIComponent(name==='Не получено'?'Не указан':name)}">${escape(name==='Не получено'?'Не указан':name)}</a></td><td>${count}</td></tr>`).join('')}</tbody></table></section><section class="panel"><h2>Технологии в документации</h2><p class="small">Количество README, где упоминается технология. В одном проекте их может быть несколько; упоминание не подтверждает использование.</p><table class="stats-table"><thead><tr><th>Технология</th><th>Проектов</th></tr></thead><tbody>${Object.entries(tech).sort((a,b)=>b[1]-a[1]).map(([name,count])=>`<tr><td>${escape(name)}</td><td>${count}</td></tr>`).join('')}</tbody></table></section></div></div>`;
 document.querySelector('#export-all').addEventListener('click',()=>exportCsv(projects));
}
function renderMethod(){
 const substantial=data.projects.filter(p=>p.readmeStatus==='found'&&!p.readmeTemplate).length;
 const templates=data.projects.filter(p=>p.readmeTemplate).length;
 main.innerHTML=`<div class="prose"><h1>Как считаем</h1>
 <section class="panel"><h2>Независимый разбор сообщества</h2><p>Каталог объединяет ${fmt(data.projects.length)} проектов в 12 кейсах. Разбор не связан с официальным жюри и не предсказывает его решение.</p><p>Сейчас каждый проект получает одну оценку GPT-5.6 Luna. На сайте и в рейтинге показана именно она.</p></section>
 <section class="panel"><h2>Какие проекты участвуют</h2><p>Берём непустые репозитории с решением одного из кейсов. Пустые шаблоны, петиции и материалы без конкурсного решения исключены. Каждый проект относится ровно к одному кейсу.</p><p>Рабочее окно: 23 сентября 2026 года, с 13:00 до 18:00 по Астане. Во время подробной проверки активность сверяется по всем веткам. Судья получает только коммиты до дедлайна; поздние изменения не оцениваются. До этой сверки включение в каталог само по себе не подтверждает активность в нужном окне.</p><p>Дисквалификация в этом разборе: нет коммитов в окне 13:00–18:00 либо первый коммит с решением появился после 18:00. Такие проекты получают 0 и не входят в топ-5 или резерв. Резерв — команды за пределами первых пяти с точно таким же баллом, как у пятой команды. Проверка участия каждого члена команды не проводится.</p></section>
 <section class="panel"><h2>Из чего складывается оценка</h2><p>GPT-5.6 Luna проверяет один проект в отдельной сессии без чужих оценок и сравнения с другими командами. Применяются пять общих критериев хакатона и собственная шкала кейса, если она опубликована. При двух шкалах итог — среднее их сумм; без шкалы кейса используется общая оценка. Это один судейский балл из 100.</p><p>Учитываются пять часов разработки, исходный код, документация и предоставленные тестовые данные. Устных презентаций и вопросов не было. Отсутствие выступления, видео и публичной демо-ссылки само по себе не снижает оценку.</p></section>
 <section class="panel"><h2>Как проверяем работу</h2><p>Репозиторий скачивается. Отдельно проверяются сборка, старт приложения и основной сценарий. Приложение, которое стартовало без внешнего API-ключа, считается запущенным. Интеграции без доступного ключа оцениваются по коду, а ограничение проверки указывается отдельно.</p><p>За отсутствие наших ключей, недоступность внешнего сервиса или ошибку проверочной среды баллы не снимаются. Снятие должно опираться на подтверждённую проблему проекта. Вывод по исходникам отделяется от результата выполненного теста. Визуальное поведение автоматически не проверяется.</p><p>Для каждого критерия доступны начисления, снятия и источники. Советы для следующего хакатона связаны с конкретными находками; если оснований для полезного совета нет, он не выдумывается.</p></section>
 <section class="panel"><h2>Рейтинг</h2><p>Готовый отчёт сразу попадает на сайт. Каталог по умолчанию сортируется по баллу, неоценённые проекты идут после оценённых и не получают ноль. В кейсе показываем первые десять результатов. Пока проверены не все команды, порядок предварительный. Первые пять и резерв выделяем только внутри каждого кейса. В общем каталоге этих отметок нет. Пока проверка продолжается, это предварительный топ среди оценённых проектов. Дополнительные фильтры не меняют состав топа. Одинаковые баллы дают одинаковое место; при равенстве на границе пятёрки порядок определяется идентификатором репозитория.</p></section>
 <section class="panel"><h2>README, технологии и команды</h2><p>В статистике README считаем документы, которые не распознаны как стартовый шаблон: сейчас ${fmt(substantial)}. Шаблонных README — ${fmt(templates)}. Это признак содержимого, а не оценка качества документации. Полный текст доступен на странице проекта.</p><p>Технологии определяются по упоминаниям в README; основной язык — по GitHub. Это не доказательство использования всех перечисленных инструментов.</p><p>Размер команды — от одного до трёх человек, ИИ и боты исключены. Используем GitHub Contributors и сверку авторов по веткам. Для 22 команд с лишними аккаунтами размер уточнён как три, исходные аккаунты видны в деталях. У трёх команд размер не установлен. Коммиты всех зарегистрированных участников пока нельзя надёжно посчитать без регистрационного списка.</p></section>
 <a class="button" href="#catalog">К проектам ${icon('arrow')}</a></div>`;
}
function notFound(){main.innerHTML='<div class="empty"><h1>Страница не найдена</h1><p>Такого проекта или кейса нет в сохранённом каталоге.</p><a class="button" href="#catalog">Открыть каталог</a></div>';}
function renderRoute(){
 const hash=(location.hash||'#catalog').slice(1);const [path,query]=hash.split('?');route=path||'catalog';params=new URLSearchParams(query||'');
 nav.innerHTML=[['catalog','Проекты'],['cases','Кейсы'],['stats','Статистика'],['method','Как считаем']].map(([id,title])=>`<a class="nav-link ${route===id||(id==='cases'&&route.startsWith('case/'))||(id==='catalog'&&route.startsWith('project/'))?'active':''}" href="#${id}" ${route===id?'aria-current="page"':''}>${title}</a>`).join('');
 if(route==='catalog')renderCatalog();else if(route==='cases')renderCases();else if(route==='stats')renderStats();else if(route==='method')renderMethod();else if(route.startsWith('project/'))renderProject(decodeURIComponent(route.slice(8)));else if(route.startsWith('case/'))renderCase(route.slice(5));else notFound();
 document.title=(route.startsWith('project/')?(data.projects.find(p=>p.id===route.slice(8))?.name||'Проект'):route==='stats'?'Статистика':route==='cases'?'Кейсы':'Проекты')+' | HackAlem';
 const restore=pendingScroll??scrollPositions.get(location.hash||'#catalog')??0;
 pendingScroll=null;
 window.scrollTo({top:restore,behavior:'instant'});
}
window.addEventListener('hashchange',()=>{if(location.hash==='#main'){main.focus();return;}if(data)renderRoute();});
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(route!=='catalog')navigate('#catalog');setTimeout(()=>document.querySelector('#search')?.focus(),0);}});
async function refreshReviews(){
 if(!data||document.hidden)return;
 try{
  const response=await fetch('./data/reviews/index.json',{cache:'no-store'});if(!response.ok)return;
  const next=await response.json(),fingerprint=JSON.stringify([next.reviews,next.partialReviews,next.eligibility]);
  if(fingerprint===reviewFingerprint)return;
  const currentReview=route.startsWith('project/')?reviewById(route.slice(8)):null;
  reviewIndex=next;reviewFingerprint=fingerprint;
  if(route.startsWith('project/')&&JSON.stringify(currentReview)===JSON.stringify(reviewById(route.slice(8))))return;
  const scroll=window.scrollY;
  const openDetails=[...main.querySelectorAll('details')].flatMap((element,index)=>element.open?[index]:[]);
  const search=document.activeElement?.id==='search';
  const selection=search?document.activeElement.selectionStart:null;
  pendingScroll=scroll;renderRoute();
  const details=main.querySelectorAll('details');for(const index of openDetails)if(details[index])details[index].open=true;
  if(search){const input=document.querySelector('#search');input?.focus();input?.setSelectionRange(selection,selection);}
  window.scrollTo({top:scroll,behavior:'instant'});
 }catch{}
}
async function init(){try{const response=await fetch('./data/catalog.json');if(!response.ok)throw new Error('HTTP '+response.status);data=await response.json();try{const reviews=await fetch('./data/reviews/index.json');if(reviews.ok)reviewIndex=await reviews.json();}catch{}reviewFingerprint=JSON.stringify([reviewIndex.reviews,reviewIndex.partialReviews,reviewIndex.eligibility]);renderRoute();if(!reviewRefreshTimer)reviewRefreshTimer=setInterval(refreshReviews,15000);}catch{main.innerHTML='<div class="empty"><h1>Каталог не загрузился</h1><p>Проверьте, запущен ли локальный сервер, и повторите попытку.</p><button class="button" id="retry">Повторить загрузку</button></div>';document.querySelector('#retry').addEventListener('click',init);}}
init();
