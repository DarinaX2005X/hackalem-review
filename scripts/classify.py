"""Collect README text, classify the agreed participant list, export local site data.

No clones, source archives, dependency installations or project execution.
Network responses and classifications are cached for resumable runs.
"""
import argparse
import concurrent.futures
import collections
import hashlib
import os
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CACHE = DATA / 'readmes'
CACHE.mkdir(exist_ok=True)

CASES = [
    (1, 'Прогноз выработки ВЭС', 'Самрук-Казына', 'Энергетика', 'Ветер и энергия'),
    (2, 'Граф денег', 'Freedom', 'Финансы', 'Финансовые связи'),
    (3, 'Career Quest', 'Halyk Bank', 'Управление', 'Развитие сотрудников'),
    (4, 'Тарифные кампании', 'Билайн', 'Телекоммуникации', 'Маркетинг тарифов'),
    (5, 'Заказы поставщикам', 'Электрокомплект', 'Логистика', 'Пополнение склада'),
    (6, 'Подбор подрядчиков', 'Firebird', 'Креативные индустрии', 'Организация событий'),
    (7, 'AI Sana Challenge Hub', 'МНВО', 'Образование', 'Бизнес и студенты'),
    (8, 'Протоколы совещаний', 'Самрук-Казына', 'Инновации', 'Встречи и поручения'),
    (9, 'Voice Router', 'Halyk Bank', 'Коммуникации', 'Голосовые сценарии'),
    (10, 'Консультант ekt.kz', 'Электрокомплект', 'Торговля', 'Помощь покупателю'),
    (11, 'Анализ оргструктуры', 'Казактелеком', 'Спецтрек', 'Структура и функции'),
    (12, 'Аким на 5 часов', 'Astana Innovations', 'Спецтрек', 'Управление городом'),
]

# Strong named-case phrases and independent domain signals; company alone never wins.
PATTERNS = {
1: [(12,r'прогноз\w*\s+(?:почасов\w*\s+)?выработ'),(12,r'agentic.{0,30}(?:ветр|wind|вэс)'),(10,r'ветроэлектростанц|wind\s*(?:power|farm|energy)|windcast|windforecast'),(6,r'\bвэс\b|\bтурбин\w*|\bturbines?\b'),(4,r'прогноз.{0,30}ветр|wind.{0,25}forecast')],
2: [(16,r'граф\s+денег|money\s*graph'),(12,r'\baml\b|отмыван\w*|laundering'),(9,r'транзакционн\w*\s+(?:сет|граф)|transaction.{0,15}(?:graph|network)'),(7,r'дроппер|дропов|финансов\w*\s+структур\w*\s+организован'),(3,r'freedom|фридом')],
3: [(16,r'career[\s_-]*quest|карьер\w*\s+квест'),(10,r'жизненн\w*\s+цикл\w*\s+сотрудник|employee\s+lifecycle'),(8,r'геймификац.{0,40}(?:карьер|сотрудник|hr)|gamif.{0,35}(?:employee|career|hr)'),(7,r'карьерн\w*\s+(?:траектор|навигатор|развити)|career\s+(?:path|growth|develop)'),(4,r'\bhr\b|онбординг|onboarding'),(2,r'halyk|халык')],
4: [(16,r'beeline|билайн'),(12,r'tariff\s+marketing|тарифн\w*\s+кампан'),(8,r'(?:смен|смены|выбор|переход).{0,20}тариф|tariff|arpu|uplift'),(5,r'абонент.{0,30}(?:кампан|сегмент)|campaign.{0,20}(?:profit|budget)')],
5: [(14,r'(?:формирован|расч[её]т|расчет|планирован).{0,25}заказ.{0,25}поставщик'),(12,r'пополнени\w*\s+склад|inventory\s+replenishment|replenishment'),(8,r'\bmoq\b|страхов\w*\s+запас|safety\s+stock'),(7,r'закуп\w*|stockpilot|supplypilot'),(6,r'остатк\w*.{0,40}продаж|продаж.{0,40}остатк'),(2,r'электрокомплект|electrocomplect')],
6: [(16,r'firebird|файрб[её]рд'),(12,r'подбор\w*\s+(?:event.\s*)?подрядчик|подрядчик\w*\s+(?:для|на)\s+мероприят'),(10,r'event.{0,25}(?:vendor|contractor)|(?:vendor|contractor).{0,25}match'),(8,r'подрядчик'),(6,r'площадк.{0,25}ведущ|ведущ.{0,25}фотограф|event.{0,10}(?:агент|agent)')],
7: [(16,r'ai[\s_-]*sana|challenge[\s_-]*hub|аи[\s_-]*сана'),(10,r'бизнес.{0,35}студент|студент.{0,35}бизнес'),(8,r'геймификац.{0,35}практическ|рейтинг\s+готовности'),(7,r'каталог\s+(?:бизнес.)?задач|м[нн]во|университет.{0,30}задач')],
8: [(16,r'автопротокол|протоколирован'),(11,r'протокол\w*\s+(?:совещан|встреч)|meeting\s+(?:minutes|protocol)|minutes\s+of\s+meeting'),(8,r'(?:совещан|встреч|meeting).{0,35}(?:поручен|action\s*items|transcri)|(?:поручен|action\s*items).{0,35}(?:совещан|meeting)'),(5,r'диаризац|diarization|транскрибац|транскрипц'),(4,r'whisper|speech.to.text')],
9: [(16,r'voice[\s_-]*router|голосов\w*\s+маршрутизатор'),(12,r'гибридн\w*\s+голосов|голосов\w*\s+(?:ai.)?робот'),(8,r'маршрутизац.{0,35}(?:сценари|реплик|голос)|intent\s+(?:routing|classif)|scenario\s+(?:routing|select)'),(7,r'сценари.{0,30}(?:реплик|llm)|голосов.{0,30}сценари'),(3,r'halyk|халык'),(3,r'voice|голосов')],
10: [(16,r'ekt\.kz'),(12,r'ассистент.{0,30}(?:электрокомплект|интернет.магазин)|консультант.{0,30}электро'),(7,r'корзин|shopping\s+cart|add.to.cart'),(6,r'каталог\w*\s+(?:товар|продукц)|product\s+catalog'),(5,r'электрокомплект|электротехнич|electrical\s+product'),(4,r'подбор\w*\s+аналог|аналог\w*\s+товар')],
11: [(16,r'казах?телеком|kazakh?telecom'),(12,r'организационн\w*\s+структур|оргструктур|org\s*structure|organizational\s+structure'),(9,r'функци.{0,35}(?:дублир|потер|отклон)|(?:дублир|потер).{0,35}функци'),(7,r'реорганизац|reorganization'),(6,r'положени.{0,35}(?:сравнен|сопостав|анализ)')],
12: [(16,r'аким\s+на\s+(?:5|пять)\s+час|akim\s+(?:for\s+)?5'),(12,r'astana\s+innovations|quality\s+of\s+life\s+score|aqols'),(11,r'симулятор.{0,25}(?:город|аким)|city\s+(?:management|simulat)|urban\s+simulat'),(8,r'городск\w*\s+бюджет|распределен.{0,25}бюджет.{0,25}город'),(5,r'аким|akim|озеленен')],
}

def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)

def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'HackAlem-community-directory/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=22) as response:
            raw=response.read(2_000_000)
            encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
            return raw.decode(encoding, errors='replace'), None
    except urllib.error.HTTPError as e:
        return None, str(e.code)
    except Exception as e:
        return None, str(e)[:180]

def collect(repo):
    path = CACHE / (repo['name'] + '.json')
    cached = load(path)
    if cached and cached.get('status') in ('found', 'missing'):
        return cached
    errors = []
    branch = urllib.parse.quote(repo['default_branch'], safe='')
    # GitHub renders these conventional locations without needing a source checkout.
    for name in ['README.md', 'readme.md', 'README.MD', 'README', 'Readme.md', '.github/README.md', 'docs/README.md']:
        url = f'https://raw.githubusercontent.com/{repo["full_name"]}/{branch}/{name}'
        text, error = fetch_text(url)
        if text is not None:
            result = {'status': 'found', 'path': name, 'url': url, 'branch': repo['default_branch'], 'text': text, 'fetchedAt': datetime.now(timezone.utc).isoformat()}
            write(path, result)
            return result
        errors.append({'path': name, 'error': error})
        if error in ('429', '403'):
            break
    result = {'status': 'missing' if all(e['error']=='404' for e in errors) else 'error', 'errors': errors}
    write(path, result)
    return result

def classify(text):
    text = text[:80000].casefold().replace('ё', 'е')
    scores=[]
    for case, patterns in PATTERNS.items():
        matches=[]
        for weight, pattern in patterns:
            match=re.search(pattern, text, flags=re.S)
            if match:
                start=max(0,match.start()-50)
                end=min(len(text),match.end()+90)
                matches.append({'weight':weight,'excerpt':re.sub(r'\s+',' ',text[start:end])})
        scores.append({'caseId':case,'score':sum(m['weight'] for m in matches),'matches':matches})
    scores.sort(key=lambda x:x['score'],reverse=True)
    best,second=scores[:2]
    confident = best['score']>=12 and best['score']-second['score']>=6
    return {'caseId':best['caseId'] if confident else None, 'method':'readme' if confident else 'unresolved', 'scores':scores[:3]}

def run(collect_enabled=True):
    inventory=load(DATA/'inventory.json')
    # The participant list agreed for this collection stage. No new commit audit here.
    participants=[r for r in inventory if r['size']>0 and r['pushed_at']>='2026-09-23T08:00:00Z']
    write(DATA/'participants.json',participants)
    if collect_enabled:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures={pool.submit(collect,r):r for r in participants}
            done=0
            for future in concurrent.futures.as_completed(futures):
                future.result()
                done+=1
                if done%100==0 or done==len(participants):
                    print(f'README {done}/{len(participants)}',flush=True)
    overrides=load(DATA/'case-overrides.json',{})
    readme_overrides=load(DATA/'readme-overrides.json',{})
    exclusions=load(DATA/'exclusions.json',{})
    projects=[]
    pending=[]
    for repo in participants:
        if repo['name'] in exclusions:
            continue
        readme=load(CACHE/(repo['name']+'.json'),{'status':'pending'})
        readme=readme_overrides.get(repo['name'],readme)
        result=classify(readme.get('text',''))
        if repo['name'] in overrides:
            result.update(overrides[repo['name']])
        team=re.sub(r'^Hackathon team repository for\s*','',repo.get('description') or '') or repo['name']
        project={'id':repo['name'],'name':team,'url':repo['html_url'],'language':repo['language'],'defaultBranch':repo['default_branch'],'readmeBranch':readme.get('branch',repo['default_branch']),'lastPush':repo['pushed_at'],'readmeStatus':readme['status'],'readmeUrl':readme.get('url'),'readmePath':readme.get('path'),'caseId':result['caseId'],'classification':result,'teamSize':None,'allMembersCommitted':None,'reviewStatus':'not_started'}
        body=readme.get('text','')
        headings=re.findall(r'^#\s+([^\n]+)',body,re.M)
        title=next((h for h in headings if not h.lower().startswith(('hack-','hackathon team repository'))),'')
        project['product']=re.sub(r'<[^>]+>|[*`_]','',title).strip()[:150]
        project['readmeTemplate']=bool(body) and len(body.strip())<220 and not project['product']
        summary=[]
        for line in body.splitlines():
            line=line.strip()
            if not line or line.startswith(('#','<','[','!','|','```','---','>')) or 'badge' in line:continue
            line=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',line)
            line=re.sub(r'[*`_]','',line)
            if len(line)>70 and not line.lower().startswith('hackathon team repository'):
                summary.append(line)
                break
        project['summary']=' '.join(summary)[:340]
        tech_patterns={'React':r'\breact\b','Next.js':r'\bnext\.?js\b','Vue':r'\bvue\b','FastAPI':r'\bfastapi\b','Django':r'\bdjango\b','Flask':r'\bflask\b','Streamlit':r'\bstreamlit\b','Node.js':r'\bnode(?:\.?js)?\b','Docker':r'\bdocker\b','PostgreSQL':r'\bpostgres(?:ql)?\b','SQLite':r'\bsqlite\b','OpenAI':r'\bopenai\b','Gemini':r'\bgemini\b','Ollama':r'\bollama\b'}
        project['technologies']=[tech for tech,pattern in tech_patterns.items() if re.search(pattern,body,re.I)]
        contributor_data=load(DATA/'contributors'/(repo['name']+'.json'),{})
        if contributor_data.get('status')=='complete':
            def is_bot(login):
                login=(login or '').casefold()
                return '[bot]' in login or login in ('claude','claude-ai','claude-code','codex','copilot','dependabot','github-actions','devin-ai-integration')
            all_contributors=contributor_data['contributors']
            members=[c['login'] for c in all_contributors if c.get('login') and c.get('type')!='Bot' and not is_bot(c['login'])]
            anonymous=[c for c in all_contributors if not c.get('login')]
            project.update({'members':members,'teamSize':len(members) if members else None,'anonymousContributors':len(anonymous),'excludedBots':[c.get('login') or c.get('name') for c in all_contributors if c.get('type')=='Bot' or is_bot(c.get('login') or c.get('name'))],'contributorsSource':contributor_data['source']})
        projects.append(project)
        if result['caseId'] is None:
            pending.append({'repo':repo['name'],'name':team,'readmeStatus':readme['status'],'scores':result['scores'],'excerpt':readme.get('text','')[:3500]})
    write(DATA/'classified.json',projects)
    write(DATA/'unresolved.json',pending)
    counts=collections.Counter(p['caseId'] for p in projects)
    cases=[]
    for id,title,owner,sector,topic in CASES:
        task=(ROOT/'cases'/str(id)/'task.txt').read_text(encoding='utf-8-sig')
        category=task.splitlines()[0].strip()
        cases.append({'id':id,'title':category,'subtitle':title,'owner':owner,'sector':category,'topic':topic,'task':task,'count':counts[id]})
    # Keep competing keyword scores internal. A published project has one case only.
    public=[]
    for p in projects:
        item=dict(p)
        original=p['classification']
        item['classification']={k:v for k,v in original.items() if k!='scores'}
        item['classification']['evidence']=next((s['matches'] for s in original.get('scores',[]) if s['caseId']==p['caseId']),[])
        public.append(item)
    result={'generatedAt':datetime.now(timezone.utc).isoformat(),'inventoryCount':len(inventory),'initialListCount':len(participants),'excludedCount':len(exclusions),'projects':public,'cases':cases,'coverage':{'classified':len(projects)-len(pending),'unresolved':len(pending),'readme':dict(collections.Counter(p['readmeStatus'] for p in projects))},'selection':{'method':'agreed_inventory','start':'2026-09-23T08:00:00Z','end':'2026-09-23T13:00:00Z','description':'Список текущего этапа: непустые репозитории с последним push не раньше начала хакатона, исключая проекты без решения одного из 12 кейсов. Проверка коммитов во всех ветках относится к следующему этапу.'}}
    write(ROOT/'web'/'data'/'catalog.json',result)
    print(json.dumps({'projects':len(projects),'classified':len(projects)-len(pending),'unresolved':len(pending),'by_case':dict(sorted((str(k),v) for k,v in counts.items())),'readme':result['coverage']['readme']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    run(not args.offline)
