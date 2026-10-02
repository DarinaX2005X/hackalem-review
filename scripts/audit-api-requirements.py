"""Inventory example configuration on every pre-deadline branch, without cloning or execution.

Only variable names and source locations are persisted. Full scans need GitHub auth.
Interrupted / rate-limited scans resume from cached metadata and completed projects.
"""

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import subprocess
import threading
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from api_requirements import PROVIDERS, candidate, extract

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/api-requirements'
DEADLINE = '2026-09-23T13:00:00Z'
MAX_BYTES = 512_000


def read(path, fallback=None):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return fallback


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def token():
    value = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if value:
        return value
    try:
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


class GitHub:
    def __init__(self, credential):
        self.credential = credential
        self.stopped = threading.Event()

    def request(self, path, raw=False):
        if self.stopped.is_set():
            raise RuntimeError('GitHub rate limit; rerun later to resume')
        headers = {'User-Agent': 'hackalem-review-config-audit',
                   'Accept': 'application/vnd.github+json'}
        base = 'https://raw.githubusercontent.com/' if raw else 'https://api.github.com/'
        if self.credential and not raw:
            headers['Authorization'] = 'Bearer ' + self.credential
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers), timeout=35) as response:
                    data = response.read(MAX_BYTES + 1) if raw else response.read()
                if raw and len(data) > MAX_BYTES:
                    raise ValueError('configuration file exceeds 512 KB')
                return data.decode('utf-8', errors='replace') if raw else json.loads(data)
            except urllib.error.HTTPError as error:
                if error.code in (403, 429):
                    self.stopped.set()
                    raise RuntimeError('GitHub access/rate limit; authorize or rerun later') from None
                if error.code < 500 or attempt == 2:
                    raise RuntimeError(f'GitHub HTTP {error.code}') from None
            except (TimeoutError, urllib.error.URLError):
                if attempt == 2:
                    raise RuntimeError('GitHub network unavailable') from None
            time.sleep(attempt + 1)

    def metadata(self, path):
        cache = OUTPUT / 'metadata' / (hashlib.sha256(path.encode()).hexdigest() + '.json')
        result = read(cache)
        if result is None:
            result = self.request(path)
            write(cache, result)
        return result

    def snapshots(self, repo):
        # One GraphQL request returns cutoff commits for all branches, avoiding
        # one REST history request per branch and conserving the core quota.
        cache = OUTPUT / 'metadata' / f'snapshots-{repo}.json'
        saved = read(cache)
        if saved is not None:
            return saved
        query = '''query($name:String!, $cursor:String, $until:GitTimestamp!) {
          repository(owner:"BAITC-Hacks", name:$name) {
            refs(refPrefix:"refs/heads/", first:100, after:$cursor) {
              pageInfo {hasNextPage endCursor}
              nodes {name target {... on Commit {history(first:1, until:$until) {nodes {oid}}}}}
            }
          }
        }'''
        result, cursor = [], None
        while True:
            if self.stopped.is_set():
                raise RuntimeError('GitHub quota exhausted; rerun later')
            body = json.dumps({'query': query, 'variables': {'name': repo, 'cursor': cursor, 'until': DEADLINE}}).encode()
            request = urllib.request.Request('https://api.github.com/graphql', data=body,
                headers={'Authorization': 'Bearer ' + self.credential, 'Content-Type': 'application/json',
                         'User-Agent': 'hackalem-review-config-audit'})
            try:
                with urllib.request.urlopen(request, timeout=35) as response:
                    data = json.load(response)
            except urllib.error.HTTPError as error:
                if error.code in (403, 429):
                    self.stopped.set()
                raise RuntimeError(f'GitHub GraphQL HTTP {error.code}') from None
            except (TimeoutError, urllib.error.URLError):
                raise RuntimeError('GitHub GraphQL network unavailable') from None
            if data.get('errors'):
                if any(e.get('type') == 'RATE_LIMITED' for e in data['errors']):
                    self.stopped.set()
                raise RuntimeError('GitHub GraphQL did not return branch history')
            repository = data.get('data', {}).get('repository')
            if not repository:
                raise RuntimeError('GitHub repository unavailable')
            refs = repository['refs']
            for ref in refs['nodes']:
                commits = ref['target'].get('history', {}).get('nodes', [])
                if commits:
                    result.append({'name': ref['name'], 'snapshot': commits[0]['oid']})
            if not refs['pageInfo']['hasNextPage']:
                break
            cursor = refs['pageInfo']['endCursor']
        write(cache, result)
        return result

    def variables(self, repo, sha, entry):
        cache = OUTPUT / 'parsed' / f'{entry["sha"]}.json'
        result = read(cache)
        if result is None:
            path = urllib.parse.quote(entry['path'], safe='/')
            result = extract(self.request(f'BAITC-Hacks/{repo}/{sha}/{path}', raw=True), entry['path'])
            # The cached result contains names only; no source text or values.
            write(cache, [{k: v for k, v in row.items() if k != 'path'} for row in result])
        return [{**row, 'path': entry['path']} for row in result]


def saved_sources(project):
    result = []
    cached = read(ROOT / 'data/discovery' / f'{project["id"]}.json', {})
    for doc in cached.get('docs', []):
        if candidate(doc.get('path', 'README.md')) and isinstance(doc.get('text'), str):
            result.extend(extract(doc['text'], doc.get('path', 'README.md')))
    path = ROOT / 'data/readmes' / f'{project["id"]}.json'
    cached = read(path, {})
    if isinstance(cached, dict):
        content = cached.get('text') or cached.get('readme') or cached.get('content')
        if isinstance(content, str):
            result.extend(extract(content, project.get('readmePath') or 'README.md'))
    return list({(row['name'], row['path'], row['line']): row for row in result}.values())


def audit(project, client):
    repo = project['id']
    path = OUTPUT / 'projects' / f'{repo}.json'
    previous = read(path, {})
    if previous.get('status') == 'complete' and previous.get('deadline') == DEADLINE:
        return previous
    result = {'repoId': repo, 'caseId': project['caseId'], 'deadline': DEADLINE,
              'status': 'partial', 'branches': [], 'files': [], 'variables': [], 'errors': []}
    if client is None:
        result['variables'] = [{**row, 'branch': 'saved-readme', 'snapshot': None}
                               for row in saved_sources(project)]
        result['errors'] = ['Only saved documentation; branch/configuration coverage is unverified']
        write(path, result)
        return result
    try:
        for branch in client.snapshots(repo):
            name = branch['name']
            sha = branch['snapshot']
            result['branches'].append({'name': name, 'snapshot': sha})
            tree = client.metadata(f'repos/BAITC-Hacks/{repo}/git/trees/{sha}?recursive=1')
            if tree.get('truncated'):
                result['errors'].append(f'{name}: GitHub truncated tree; coverage incomplete')
            for entry in tree.get('tree', []):
                if entry.get('type') != 'blob' or not candidate(entry['path']):
                    continue
                location = {'path': entry['path'], 'branch': name, 'snapshot': sha}
                try:
                    if entry.get('size', 0) > MAX_BYTES:
                        raise ValueError('file exceeds 512 KB')
                    variables = client.variables(repo, sha, entry)
                    result['files'].append(location)
                    result['variables'].extend({**row, 'branch': name, 'snapshot': sha} for row in variables)
                except (RuntimeError, ValueError) as error:
                    result['errors'].append(f'{name}/{entry["path"]}: {error}')
                    if client.stopped.is_set():
                        raise
        if not result['branches']:
            result['errors'].append('No accessible pre-deadline branch snapshot')
        result['status'] = 'partial' if result['errors'] else 'complete'
    except (RuntimeError, ValueError, KeyError) as error:
        result['errors'].append(str(error))
    result['updatedAt'] = datetime.now(timezone.utc).isoformat()
    write(path, result)
    return result


def export(projects):
    rows = [read(OUTPUT / 'projects' / f'{p["id"]}.json',
                 {'repoId': p['id'], 'caseId': p['caseId'], 'status': 'not_scanned', 'variables': []})
            for p in projects]
    services = defaultdict(lambda: {'repos': set(), 'names': set()})
    flat = []
    for row in rows:
        for item in row['variables']:
            if item['kind'] in ('setting', 'local_service', 'local_secret'):
                continue
            p = item.get('provider') or 'unknown'
            services[p]['repos'].add(row['repoId'])
            services[p]['names'].add(item['name'])
            flat.append({'repoId': row['repoId'], 'caseId': row['caseId'], **item})
    summary = {'deadline': DEADLINE, 'projects': len(rows),
               'coverage': dict(Counter(row['status'] for row in rows)),
               'services': [{'provider': p, 'label': PROVIDERS[p][0],
                             'projects': len(info['repos']), 'variables': sorted(info['names'])}
                            for p, info in sorted(services.items(), key=lambda pair: -len(pair[1]['repos']))]}
    write(OUTPUT / 'summary.json', summary)
    columns = ['repoId', 'caseId', 'provider', 'name', 'kind', 'required', 'branch', 'snapshot', 'path', 'line']
    with (OUTPUT / 'requirements.csv').open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows({key: "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r'))
                          else value for key, value in row.items()} for row in flat)
    text = ['# API и конфигурация проектов', '', f'Каталог: {len(rows)} проектов. Покрытие: {summary["coverage"]}.',
            '', 'Собраны имена переменных, без значений. Наличие переменной не доказывает обязательность сервиса.',
            'Отсутствие примеров не доказывает отсутствие API. Назначение неоднозначных ключей и альтернативные провайдеры требуют уточнения.',
            'Supabase/Firebase/Azure и OAuth могут требовать отдельные ресурсы, endpoint, права и данные: одного ключа недостаточно.',
            '', '| Сервис | Проектов | Переменные |', '| --- | ---: | --- |']
    for item in summary['services']:
        text.append(f'| {item["label"]} | {item["projects"]} | {", ".join(item["variables"])} |')
    text += ['', 'Подробности по репозиториям: `requirements.csv`; недочитанные ветки/файлы: `projects/*.json`.']
    (OUTPUT / 'summary.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    template = ['# Только локальные тестовые credentials. Не используйте production-ключи.',
                '# Скопируйте в .env.judging.local в корне проекта; значения не попадают в отчёты.',
                '# Этот список — для подготовки. Ключи пока НЕ передаются участникам автоматически.']
    for p in services:
        if PROVIDERS[p][1]:
            template += [f'\n# {PROVIDERS[p][0]}', PROVIDERS[p][1] + '=']
    (OUTPUT / 'credentials.example.env').write_text('\n'.join(template) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-only', action='store_true', help='no network; incomplete baseline from existing documentation')
    parser.add_argument('--case', type=int, choices=range(1, 13))
    parser.add_argument('--parallel', type=int, choices=range(1, 13), default=4)
    args = parser.parse_args()
    projects = read(ROOT / 'web/data/catalog.json')['projects']
    selected = [p for p in projects if args.case is None or p['caseId'] == args.case]
    credential = token() if not args.saved_only else None
    if not args.saved_only and not credential:
        parser.error('Run gh auth login, or set GH_TOKEN locally. --saved-only makes an incomplete offline baseline.')
    client = None if args.saved_only else GitHub(credential)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        pending = {}
        queue = iter(selected)
        def submit():
            project = next(queue, None)
            if project:
                pending[pool.submit(audit, project, client)] = project['id']
        for _ in range(args.parallel):
            submit()
        finished = 0
        while pending:
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                future.result()
                finished += 1
                if finished % 25 == 0:
                    export(projects)
                    print(f'Inventory {finished}/{len(selected)}', flush=True)
                if client is None or not client.stopped.is_set():
                    submit()
    print(json.dumps(export(projects), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
