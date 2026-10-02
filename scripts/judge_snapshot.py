"""Explicit, evidence-backed exceptions for incorrectly dated Git commits."""
import json
import re
from datetime import datetime,timezone

END=datetime(2026,9,23,13,tzinfo=timezone.utc)


def override(root,repo_id):
    path=root/'data/snapshot-overrides.json'
    if not path.exists():return None
    row=json.loads(path.read_text(encoding='utf-8')).get(repo_id)
    if not row:return None
    evidence=row.get('evidence',{})
    pushed=datetime.fromisoformat(evidence.get('pushedAt','').replace('Z','+00:00'))
    if (not re.fullmatch(r'[a-f0-9]{40}',row.get('snapshot','')) or
        evidence.get('archived') is not True or pushed>END or
        evidence.get('url')!='https://api.github.com/repos/BAITC-Hacks/'+repo_id):
        raise ValueError('Invalid snapshot time evidence: '+repo_id)
    return row


def apply(branches,row,clone,git):
    if not row:return branches
    # Require the exact audited object to exist, rather than silently selecting
    # a newer branch head. Never rewrite author or committer timestamps.
    if git('rev-parse',row['snapshot']+'^{commit}',cwd=clone)!=row['snapshot']:
        raise ValueError('Audited snapshot is unavailable')
    return [b for b in branches if b['name']!=row['branch']]+[
        {'name':row['branch'],'commit':row['snapshot']}]


def prompt_note(row):
    if not row:return ''
    return ('Важное уточнение времени среза: для этого репозитория проверена ошибка дат Git. '
        'GitHub API показывает последний push '+row['evidence']['pushedAt']+
        ', до дедлайна; репозиторий архивирован. Проверенный SHA '+row['snapshot']+
        ' уже находился на GitHub до дедлайна, хотя локальные даты коммитов с поясом -07:00 '
        'указывают будущее время. Разрешено и необходимо оценить весь этот SHA. '
        'Не откатывайся к раннему README и не штрафуй за ошибочные часы Git. '
        'Доказательства сохранены в snapshotTimeEvidence манифеста; исходные даты не изменены.')
