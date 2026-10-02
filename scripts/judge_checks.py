"""Keep small, snapshot-scoped records of successful mechanical judge checks."""

import hashlib
import json
import os
import re
from pathlib import Path

CHECKS = (
    ('build', re.compile(r'\b(?:docker\s+(?:image\s+)?build|docker\s+compose\s+build|npm\s+run\s+build|pnpm\s+build|yarn\s+build|cargo\s+build|go\s+build|mvn\s+package)\b', re.I)),
    ('start', re.compile(r'\b(?:docker\s+(?:container\s+)?run|docker\s+compose\s+up|uvicorn|gunicorn|npm\s+(?:run\s+)?(?:start|dev)|pnpm\s+(?:start|dev)|yarn\s+(?:start|dev))\b', re.I)),
    ('test', re.compile(r'\b(?:pytest|unittest|npm\s+test|npm\s+run\s+test|pnpm\s+test|yarn\s+test|go\s+test|cargo\s+test|curl|Invoke-WebRequest|Invoke-RestMethod|local_eval\.py|make_submission\.py)\b', re.I)),
)
SECRET = re.compile(r'(?i)(authorization\s*[:=]\s*|(?:api[_-]?key|token|password|passwd|secret)\s*[:=]\s*)([^\s;]+)')
BEARER = re.compile(r'(?i)(bearer\s+)[a-z0-9._~+/-]+')
CURL_USER = re.compile(r'(?i)(\bcurl(?:\.exe)?\b[^\r\n]*?\s+-u\s+)[^\s]+')


def redact(value):
    value = BEARER.sub(lambda match: match.group(1)+'[redacted]', value)
    value = SECRET.sub(lambda match: match.group(1)+'[redacted]', value)
    return CURL_USER.sub(lambda match: match.group(1)+'[redacted]', value)


def category(command):
    for label, pattern in CHECKS:
        if pattern.search(command):
            return label
    return None


def read(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_successes(destination, snapshot, events):
    """Append completed zero-exit command events; never infer that a scenario passed."""
    state = read(destination)
    if state.get('snapshot') != snapshot:
        state = {'snapshot':snapshot, 'checks':[]}
    known = {row['id'] for row in state['checks']}
    try:
        source = events.open(encoding='utf-8', errors='replace')
    except OSError:
        return state
    with source:
        for line in source:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') != 'item.completed':
                continue
            item = event.get('item')
            if not isinstance(item, dict) or item.get('type') != 'command_execution':
                continue
            if item.get('exit_code') != 0:
                continue
            command = item.get('command')
            if not isinstance(command, str):
                continue
            kind = category(command)
            if not kind:
                continue
            identity = hashlib.sha256((snapshot+'\n'+command).encode('utf-8')).hexdigest()[:20]
            if identity in known:
                continue
            state['checks'].append({'id':identity, 'kind':kind, 'command':redact(command)[:300],
                                    'exitCode':0,
                                    'events':str(events)})
            known.add(identity)
    state['checks'] = state['checks'][-80:]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix+'.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, destination)
    return state


def resume_note(destination, snapshot):
    state = read(destination)
    if state.get('snapshot') != snapshot or not state.get('checks'):
        return f'Журнал успешных технических команд пока пуст: {destination}.'
    recent = state['checks'][-10:]
    lines = [f'Журнал уже завершённых команд для этого среза: {destination}.',
             'Запись exitCode=0 доказывает только успешное завершение команды, не качество сценария. '
             'Сверься с полным логом при сомнении; повторяй шаг только если он нужен для дальнейшего теста.']
    for item in recent:
        lines.append(f'- {item["kind"]}: {item["command"]} (exit 0; лог {item["events"]})')
    if len(state['checks']) > len(recent):
        lines.append(f'- Ещё {len(state["checks"])-len(recent)} записей в журнале.')
    return '\n'.join(lines)
