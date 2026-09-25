from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web'/'app.js'
s=p.read_text(encoding='utf-8')
s=s.replace("${escape(caseById(p.caseId)?.owner||'Нужен дополнительный источник')}","${escape(caseById(p.caseId)?.subtitle||'')}")
s=s.replace("${escape(c.owner)}</span><p>","${escape(c.subtitle)}</span><span class=\"case-company\">${escape(c.owner)}</span><p>")
s=s.replace("<p class=\"subtitle\">${escape(c.owner)}<br>${escape(c.sector)}</p>","<p class=\"subtitle\">${escape(c.subtitle)}<br><span class=\"small\">${escape(c.owner)}</span></p>")
s=s.replace("<span>${escape(title)}</span><span class=\"count\">", "<span>${escape(title)}${caseById(id)?`<small class=\"case-subtitle\">${escape(caseById(id).subtitle)}</small>`:''}</span><span class=\"count\">")
s=s.replace("c?', '+escape(c.owner)","c?', '+escape(c.subtitle)")
s=s.replace("['Команда','Проект','Кейс','Заказчик'", "['Команда','Проект','Категория','Кейс','Заказчик'")
s=s.replace("p.product,caseTitle(p),caseById(p.caseId)?.owner", "p.product,caseTitle(p),caseById(p.caseId)?.subtitle,caseById(p.caseId)?.owner")
s=s.replace("<a href=\"#case/${c.id}\">${escape(c.title)}</a>","<a href=\"#case/${c.id}\">${escape(c.title)}<span class=\"case-owner\">${escape(c.subtitle)}</span></a>")
p.write_text(s,encoding='utf-8')
style=ROOT/'web'/'style.css'
css=style.read_text(encoding='utf-8')
if '.case-subtitle{' not in css:css+='\n.case-subtitle{display:block;font-size:10px;font-weight:450;line-height:1.55;color:var(--muted);margin-top:2px}.case-company{font-size:11px;color:var(--muted);margin:-12px 0 19px}.case-card .owner{font-size:14px;color:var(--ink);line-height:1.6}\n'
style.write_text(css,encoding='utf-8')
print('Case categories and subtitles updated')
