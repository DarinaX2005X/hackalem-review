"""Apply human-reviewed team counts, preserving uncertainty and GitHub author evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'web/data/catalog.json'
catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
audit = {row['id']:row for row in json.loads((ROOT/'data/team-audit.json').read_text(encoding='utf-8'))}

def distinct_people(row):
    names = []
    for author in row['humanAuthors']:
        name = author['names'][0].strip()
        if name.casefold() not in {x.casefold() for x in names}:
            names.append(name)
    return names

for project in catalog['projects']:
    row = audit.get(project['id'])
    if not row:
        continue
    if project['teamSize'] is not None and project['teamSize'] > 3:
        project['contributorsCount'] = project['teamSize']
        project['teamSize'] = 3
        project['teamSizeSource'] = 'confirmed_team_limit'
        project['teamSizeNote'] = ('Состав из трёх участников уточнён вручную. В GitHub Contributors больше аккаунтов: '
                                   'есть альтернативные подписи и/или дополнительные авторы. '
                                   'Точное соответствие каждого аккаунта зарегистрированному участнику не подтверждено.')
        continue
    if project['teamSize'] is None:
        people = distinct_people(row)
        project['anonymousMembers'] = people
        if 1 <= len(people) <= 3:
            project['teamSize'] = len(people)
            project['teamSizeSource'] = 'git_author_signatures'
            project['teamSizeNote'] = ('Оценка по уникальным человеческим подписям автора во всех ветках до дедлайна. '
                                       'GitHub не связывает эти подписи с профилями, поэтому зарегистрированный состав отдельно не подтверждён.')
        else:
            project['teamSizeSource'] = 'unresolved_ai_only' if not people else 'unresolved_authors'
            project['teamSizeNote'] = 'В доступной истории до дедлайна не удалось установить человеческих авторов коммитов.'

CATALOG.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
from collections import Counter
print('Team sizes:',dict(sorted(Counter(str(p['teamSize']) for p in catalog['projects']).items())))
