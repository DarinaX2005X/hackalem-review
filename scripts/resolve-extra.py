from classify import DATA,load,write,fetch_text
import pathlib,re,urllib.parse,concurrent.futures,subprocess,json

rows=load(DATA/'unresolved-initial.json')
overrides=load(DATA/'case-overrides.json',{})
decisions={14:(10,'Описание EKT AI-консультанта в README вложенной папки проекта.'),16:(7,'README soile-platform описывает задачи бизнеса и студенческие команды.'),23:(12,'README backend/frontend описывают районы, бюджет и выбор пяти решений.'),42:(7,'README oqucat-client описывает маркетплейс бизнес-задач для студенческих команд.'),54:(6,'README Creative I прямо называет кейс 79-lite и подбор подрядчиков.'),58:(2,'README_Money_Graph.md прямо описывает Money Graph AML.'),71:(10,'Архивы ekt-ai-agent.zip и ekt-repeat-source.zip указывают на EKT. Назначение предварительное, архивы не распаковывались.'),88:(12,'README QALA_LAB называет кейс «5 сағатқа әкім».'),94:(6,'Архив smart-event-match.zip указывает на подбор event-подрядчиков. Назначение предварительное.'),108:(7,'README-TaskForge.md описывает карточки бизнес-задач и выбор студенческих команд.'),113:(12,'README Akimator.ai прямо называет «Аким на 5 часов».'),122:(7,'Учебная платформа BLITZ отнесена к образовательному кейсу по тематике; точное соответствие задаче не утверждается.'),134:(10,'README Hackalemai-main и название приложенного задания указывают на консультанта ekt.kz.'),140:(6,'Название архива jina-event-matcher.zip указывает на подбор event-подрядчиков. Назначение предварительное.'),148:(8,'README нескольких вложенных проектов описывают протоколирование встреч.'),151:(12,'GovBrain и городской контекст требуют подтверждения по HTML проекта.')}
for index,(case,reason) in decisions.items():
    overrides[rows[index]['repo']]={'caseId':case,'method':'manual','reason':reason,'source':'README / directory listing','provisional':index in (71,94,122,140,151)}
write(DATA/'case-overrides.json',overrides)

inventory={x['name']:x for x in load(DATA/'participants.json')}
dest=DATA/'extra'
dest.mkdir(exist_ok=True)
# Only small, relevant text files observed in repository listings; no archives or secrets.
files={39:['index.html','script.js'],71:['REVIEW.md'],94:['main.py'],114:['MY_FIRST_GITHUB_FILE.md','TRAINING_01.md'],125:['index.html','script.js'],151:['GovBrain.html','govbrain_ai_platform (1).html']}
for index,paths in files.items():
    repo=inventory[rows[index]['repo']]
    docs=[]
    for path in paths:
        url=f'https://raw.githubusercontent.com/{repo["full_name"]}/{urllib.parse.quote(repo["default_branch"],safe="")}/{urllib.parse.quote(path)}'
        text,error=fetch_text(url)
        if text:docs.append({'path':path,'text':text,'url':url})
    write(dest/(repo['name']+'.json'),{'docs':docs})

def branches(repo):
    path=dest/(repo['name']+'-branches.json')
    if path.exists():return
    result=subprocess.run(['git','ls-remote','--heads','https://github.com/'+repo['full_name']+'.git'],capture_output=True,text=True,timeout=40)
    names=[line.split('refs/heads/',1)[1] for line in result.stdout.splitlines() if 'refs/heads/' in line]
    docs=[]
    for branch in names[:25]:
        if branch==repo['default_branch']:continue
        url=f'https://raw.githubusercontent.com/{repo["full_name"]}/{urllib.parse.quote(branch,safe="")}/README.md'
        text,error=fetch_text(url)
        if text:docs.append({'branch':branch,'text':text,'url':url})
    write(path,{'branches':names,'docs':docs,'error':result.stderr[:200] if result.returncode else None})
pending=[inventory[x['repo']] for x in rows if x['repo'] not in overrides]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for _ in pool.map(branches,pending):pass
print('Additional documents and branch README collection complete',flush=True)
