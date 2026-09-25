from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web'/'app.js'
s=p.read_text(encoding='utf-8')
s=s.replace(",['unknown','Кейс уточняется']",'')
s=s.replace('Если в материалах недостаточно сведений или описано несколько кейсов, мы показываем это явно. Совпадение с кейсом не означает, что требования выполнены: это проверят судьи.','Каждому включённому проекту назначен ровно один кейс. Репозитории без конкурсного решения исключены из каталога и не считаются участниками. Совпадение с кейсом не означает, что требования выполнены: это проверят судьи.')
s=s.replace('непустых репозиториев с последним push не раньше 23 сентября 2026, 13:00 по Астане.','репозиториев с решениями кейсов. Исходный список содержал ${fmt(data.initialListCount)} непустых репозиториев с последним push не раньше 23 сентября 2026, 13:00 по Астане. После чтения материалов исключено ${data.excludedCount} репозиториев без конкурсного решения.')
s=s.replace('Состав команды берём из публичного списка GitHub Contributors.','Состав команды берём из публичного списка GitHub Contributors: считаем аккаунты GitHub, к которым привязано авторство.')
s=s.replace('Дополнительных авторов из других веток и коммиты каждого участника','Непривязанные к аккаунту подписи авторов не считаем отдельными зарегистрированными участниками, чтобы не дублировать одного человека. Дополнительных авторов из других веток и коммиты каждого участника')
s=s.replace("<a class=\"back\" href=\"${escape(backTo)}\">", "<a class=\"back\" href=\"${escape(backTo)}\">")
# A hash used as a skip target must not invoke the router.
s=s.replace("window.addEventListener('hashchange',()=>{if(data)renderRoute();});", "window.addEventListener('hashchange',()=>{if(location.hash==='#main'){main.focus();return;}if(data)renderRoute();});")
p.write_text(s,encoding='utf-8')
print('Final public copy saved')
