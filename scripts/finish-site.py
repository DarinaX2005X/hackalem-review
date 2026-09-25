from classify import DATA,ROOT,load,write
import pathlib,re,shutil

overrides=load(DATA/'case-overrides.json',{})
overrides['hack-0273c87f-idahar']={'caseId':7,'method':'manual','reason':'README mvp/README.md в ветке codex/hackalem-mvp описывает SanaQuest и рейтинг готовности бизнес-задач.','source':'mvp/README.md'}
overrides['hack-6c1cc162-qwertl06ang']={'caseId':6,'method':'manual','reason':'CSV_UPDATE.md описывает каталог подрядчиков, категории событий, свободные даты, цены и ранжирование вариантов.','source':'hackalem/CSV_UPDATE.md'}
overrides['hack-87fade6d-4-0-4']={'caseId':10,'method':'manual','reason':'REVIEW.md описывает доработку EKT-консультанта: свободный чат, каталог товаров, аналоги и корзина.','source':'REVIEW.md'}
excluded=load(DATA/'exclusions.json',{})
for name,reason in {
 'hack-8fa76ac5-aul-ai':'Общий сайт складской логистики, нет описания задачи расчёта заказов поставщикам или другого кейса.',
 'hack-8de246a5-zenith':'Персональный финансовый ассистент, не задача анализа транзакционной сети одного из 12 кейсов.',
 'hack-3263a402-ctrl-c':'Персональная учебная платформа по произвольным темам, не задача бизнеса и студенческих команд из кейса.'
}.items():
    excluded[name]={'reason':reason,'source':'README и документация проекта'}
    overrides.pop(name,None)
write(DATA/'case-overrides.json',overrides)
write(DATA/'exclusions.json',excluded)

# All public assets must work both on localhost and under /hackalem-review/.
for name in ('index.html','style.css','app.js'):
    path=ROOT/'web'/name
    text=path.read_text(encoding='utf-8')
    text=text.replace('href="/favicon.svg"','href="./favicon.svg"').replace('href="/style.css"','href="./style.css"').replace('src="/app.js"','src="./app.js"').replace("url('/fonts/Manrope.ttf')","url('./fonts/Manrope.ttf')").replace("fetch('/data/catalog.json')","fetch('./data/catalog.json')")
    text=text.replace('HackAlem • Каталог проектов','HackAlem | Каталог проектов')
    text=text.replace("(p.classification.scores?.find(s=>s.caseId===p.caseId)?.matches||[])","(p.classification.evidence||[])")
    text=text.replace("' · '+escape(c.owner)","', '+escape(c.owner)")
    path.write_text(text,encoding='utf-8')
print('Final case assignments and relative asset paths saved')
