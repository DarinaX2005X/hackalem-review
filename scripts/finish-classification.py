from classify import DATA,load,write,fetch_text,classify
from github_api import credential,request
import re,urllib.parse

rows=load(DATA/'unresolved-initial.json')
overrides=load(DATA/'case-overrides.json',{})
decisions={24:(1,'Основным кейсом выбран прогноз ВЭС: первое решение ZHEL.ai в README и отдельная папка zhel-ai. Репозиторий учитывается один раз.'),28:(7,'В README явно заявлена образовательная тема; реализация решения не найдена.'),33:(5,'Складская логистика Arna Logistics отнесена к кейсу пополнения склада по предметной области. Выполнение условий не утверждается.'),34:(2,'Финансовый ассистент «Теңге» отнесён к финансовому кейсу по предметной области. Совпадение с требованиями графа денег не утверждается.'),53:(11,'Рабочая ветка orglens-app содержит решение OrgLens для анализа организационной структуры.'),90:(2,'README ветки backend-agent описывает транзакционный граф, роли и nodes_roles.csv.'),94:(9,'main.py объявляет Halyk Voice Router API и маршрутизацию голосовых банковских обращений. Содержимое кода имеет приоритет над именем старого архива.'),114:(3,'Ветка submission-final прямо указывает Career Quest, трек 03 «Управление».'),117:(7,'README feature/frontend прямо указывает AI Sana Challenge Hub.'),118:(10,'README ветки ekt-ai описывает консультанта ekt.kz.'),121:(10,'README рабочих веток описывает EKT каталог, поиск, карточки и AI-чат.'),125:(10,'index.html содержит EKT AI Assistant, электротовары и корзину.'),126:(10,'README codex/final-integration и других рабочих веток описывают EKT AI.'),135:(7,'README feat/backend и feat/frontend описывает TASKER, платформу задач бизнеса для студенческих команд.'),136:(12,'README codex/cityproof прямо указывает «Аким на 5 часов».'),151:(12,'HTML GovBrain содержит карту города, городской бюджет и выбор проектов.')}
for i,(case,reason) in decisions.items():
    overrides[rows[i]['repo']]={'caseId':case,'method':'manual','reason':reason,'source':'README / project entry file'}

# Explicit exclusions authorized by the user: no solution to a hackathon case.
excluded=load(DATA/'exclusions.json',{})
for i,reason in {28:'Только README без решения кейса.',39:'Страница о недопуске на мероприятие, вне 12 кейсов.',105:'Только шаблонный README, решения кейса не найдено.',124:'Платформа петиций против организаторов, вне 12 кейсов.',153:'Нет доступных веток и исходных файлов решения.'}.items():
    excluded[rows[i]['repo']]={'reason':reason,'source':'README, список файлов и доступных веток'}
    overrides.pop(rows[i]['repo'],None)
write(DATA/'case-overrides.json',overrides)
write(DATA/'exclusions.json',excluded)

# Save exact readme selection for projects whose main README is only a placeholder.
selected=load(DATA/'readme-overrides.json',{})
for i,row in enumerate(rows):
    name=row['repo']
    if name not in overrides:continue
    original=load(DATA/'readmes'/(name+'.json'),{})
    sources=load(DATA/'discovery'/(name+'.json'),{}).get('docs',[])+load(DATA/'extra'/(name+'-branches.json'),{}).get('docs',[])
    if name=='hack-5e5a1903-mg-ai':
        sources=[d for d in sources if d.get('path')=='zhel-ai/README.md']
    if len(original.get('text',''))>500 and name!='hack-5e5a1903-mg-ai':continue
    useful=[d for d in sources if len(d.get('text',''))>300 and (classify(d['text'])['caseId']==overrides[name]['caseId'])]
    if not useful:useful=[d for d in sources if len(d.get('text',''))>300]
    if useful:
        doc=useful[0]
        selected[name]={'status':'found','path':doc.get('path','README.md'),'branch':doc.get('branch',original.get('branch','main')),'url':doc['url'],'text':doc['text']}
write(DATA/'readme-overrides.json',selected)

# For the last uncertain repositories, fetch file NAMES from observed branches only.
token=credential()
for i in (53,82,150,153):
    name=rows[i]['repo']
    branches=load(DATA/'extra'/(name+'-branches.json'),{}).get('branches',[])
    output=[]
    for branch in branches:
        try:
            tree=request(f'repos/BAITC-Hacks/{name}/git/trees/{urllib.parse.quote(branch,safe="")}?recursive=1',token=token)
            output.append({'branch':branch,'paths':[x['path'] for x in tree.get('tree',[]) if x['type']=='blob']})
        except Exception as e:output.append({'branch':branch,'error':str(e)[:200]})
    write(DATA/'extra'/(name+'-paths.json'),output)
print('Decisions',len(overrides),'excluded',len(excluded),'selected README',len(selected))
