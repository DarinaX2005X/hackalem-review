"""Make a compact, neutral project inventory before either judge starts.

Only Git metadata and dataset headers are read. Participant code is never run here.
"""

import csv
import hashlib
import json
import os
import re
import subprocess
import threading
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('D:/hackalem-review-work')
DATA_SUFFIXES = {'.csv', '.json', '.jsonl', '.parquet', '.xlsx', '.xls', '.mp3', '.wav'}
SOURCE_SUFFIXES = {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java', '.kt', '.vue', '.svelte', '.html'}
CONFIG_NAMES = {'package.json', 'pyproject.toml', 'requirements.txt', 'pipfile', 'poetry.lock',
                'dockerfile', 'compose.yml', 'compose.yaml', 'docker-compose.yml',
                'docker-compose.yaml', 'go.mod', 'cargo.toml', 'pom.xml', 'build.gradle',
                'vite.config.ts', 'vite.config.js', 'next.config.js', 'next.config.mjs',
                'next.config.ts', '.env.example'}
SKIP_PARTS = {'node_modules', '.venv', 'venv', 'vendor', 'dist', 'build', '.next', '.git'}


def git(repo, *args):
    result = subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=120,
                            env={**os.environ, 'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:
        raise RuntimeError(f'git {args[0]} failed: {result.stderr[-300:]}')
    return result.stdout


def safe_name(value):
    return re.sub(r'[\r\n\t`<>]', '_', value)[:160]


def file_entries(repo, snapshot):
    rows = []
    for record in git(repo, 'ls-tree', '-r', '-l', '-z', snapshot).split('\0'):
        if not record or '\t' not in record:
            continue
        metadata, name = record.split('\t', 1)
        fields = metadata.split()
        if len(fields) != 4 or fields[1] != 'blob':
            continue
        rows.append({'path':name, 'bytes':int(fields[3]) if fields[3].isdigit() else None})
    return rows


def file_group(entries, predicate, limit):
    paths = sorted((entry['path'] for entry in entries if predicate(entry['path'])),
                   key=lambda path:(path.count('/'), path.casefold()))
    shown = ', '.join(f'`{safe_name(path)}`' for path in paths[:limit]) or 'нет'
    return shown + (f' (ещё {len(paths)-limit}; полный список в inventory.json)' if len(paths)>limit else '')


def case_data_index(case_id, work=WORK, root=ROOT):
    case_root = root/'cases'/str(case_id)/'case-data'
    files = sorted(path for path in case_root.rglob('*') if path.is_file() and path.suffix.lower() in DATA_SUFFIXES)
    fingerprint = hashlib.sha256('\n'.join(f'{path.relative_to(case_root)}:{path.stat().st_size}:{path.stat().st_mtime_ns}'
                                          for path in files).encode('utf-8')).hexdigest()
    output = work/'case-index'/f'{case_id:02}.json'
    if output.is_file():
        try:
            existing = json.loads(output.read_text(encoding='utf-8'))
            if existing.get('fingerprint') == fingerprint:
                return existing, output
        except (OSError, ValueError):
            pass
    datasets = []
    for path in files:
        entry = {'path':path.relative_to(case_root).as_posix(), 'bytes':path.stat().st_size,
                 'format':path.suffix.lower().lstrip('.')}
        try:
            if path.suffix.lower() == '.csv':
                with path.open(encoding='utf-8-sig', errors='replace', newline='') as source:
                    entry['columns'] = next(csv.reader(source), [])[:30]
            elif path.suffix.lower() == '.json' and path.stat().st_size <= 2_000_000:
                data = json.loads(path.read_text(encoding='utf-8-sig'))
                entry['shape'] = ('object' if isinstance(data, dict) else
                                  'array' if isinstance(data, list) else type(data).__name__)
                if isinstance(data, dict):
                    entry['keys'] = list(data)[:30]
                elif isinstance(data, list):
                    entry['items'] = len(data)
                    if data and isinstance(data[0], dict):
                        entry['keys'] = list(data[0])[:30]
            elif path.suffix.lower() == '.xlsx':
                with zipfile.ZipFile(path) as archive:
                    book = ElementTree.fromstring(archive.read('xl/workbook.xml'))
                    entry['sheets'] = [node.attrib.get('name', '') for node in
                                       book.findall('.//{*}sheet')][:20]
        except (OSError, UnicodeError, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as error:
            entry['metadataError'] = type(error).__name__
        datasets.append(entry)
    result = {'caseId':case_id, 'fingerprint':fingerprint, 'datasets':datasets}
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f'{output.name}.{os.getpid()}-{threading.get_ident()}.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, output)
    return result, output


def build_dossier(project, clone, snapshot, branches, commits, work=WORK, root=ROOT):
    """Cache an exact-snapshot inventory for both independent judges."""
    repo_id = project['id']
    case_index, index_path = case_data_index(project['caseId'], work, root)
    folder = work/'dossiers'/repo_id
    folder.mkdir(parents=True, exist_ok=True)
    markdown = folder/f'{snapshot}.md'
    inventory = folder/f'{snapshot}-inventory.json'
    marker = f'<!-- case-index:{case_index["fingerprint"]} -->'
    if markdown.is_file() and inventory.is_file():
        with markdown.open(encoding='utf-8') as source:
            if source.readline().strip() == marker:
                return markdown
    entries = file_entries(clone, snapshot)
    ext = Counter(Path(row['path']).suffix.lower() or '(без расширения)' for row in entries)
    top = Counter(row['path'].split('/', 1)[0] for row in entries if '/' in row['path'])
    branch_changes = []
    for branch in branches:
        if branch['commit'] == snapshot:
            continue
        # Inventory needs changed paths, not content similarity. Rename detection
        # can fetch missing blobs from other branches of a blob:none clone.
        changed = [path for path in git(clone, 'diff', '--no-renames', '--no-ext-diff',
                                       '--no-textconv', '--name-only', '-z',
                                       snapshot, branch['commit'], '--').split('\0') if path]
        branch_changes.append({'branch':branch['name'], 'commit':branch['commit'],
                               'changedCount':len(changed), 'sample':changed[:20]})
    package_scripts = []
    for row in entries:
        path = row['path']
        if Path(path).name.lower() != 'package.json' or path.count('/') > 2 or len(package_scripts) >= 5:
            continue
        try:
            data = json.loads(git(clone, 'show', f'{snapshot}:{path}'))
            if isinstance(data, dict):
                package_scripts.append({'path':path, 'scriptNames':list(data.get('scripts', {}))[:20]})
        except (ValueError, RuntimeError):
            pass
    record = {'repoId':repo_id, 'caseId':project['caseId'], 'snapshot':snapshot,
              'fileCount':len(entries), 'trackedBytes':sum(row['bytes'] or 0 for row in entries),
              'extensions':dict(ext.most_common(20)), 'topDirectories':dict(top.most_common(12)),
              'files':entries, 'branches':branches, 'branchChanges':branch_changes,
              'windowCommitCount':len(commits), 'windowAuthors':dict(Counter(row['author'] for row in commits)),
              'packageScripts':package_scripts, 'caseDataIndex':str(index_path),
              'caseDataFingerprint':case_index['fingerprint']}
    inventory.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    relevant = [row for row in entries if not set(Path(row['path']).parts) & SKIP_PARTS]
    lines = [marker, f'# Техническое досье: {repo_id}',
             'Автоматически собранные факты без запуска кода и без оценки качества. '
             'Исходник — указанный срез Git; наличие файла не доказывает работоспособность.',
             f'- Срез: `{snapshot}`; кейс {project["caseId"]}; файлов: {len(entries)}; '
             f'объём отслеживаемых файлов: {record["trackedBytes"]} байт.',
             f'- Расширения: {", ".join(f"{name} {count}" for name,count in ext.most_common(12))}.',
             f'- Каталоги верхнего уровня: {", ".join(f"{safe_name(name)} {count}" for name,count in top.most_common(10)) or "нет"}.',
             f'- README: {file_group(relevant, lambda p: Path(p).name.casefold().startswith("readme"), 12)}.',
             f'- Конфигурация/запуск: {file_group(relevant, lambda p: Path(p).name.casefold() in CONFIG_NAMES, 25)}.',
             f'- Основные исходники: {file_group(relevant, lambda p: Path(p).suffix.lower() in SOURCE_SUFFIXES, 70)}.',
             f'- Тесты: {file_group(relevant, lambda p: bool(re.search(r"(^|/)(test|tests|spec|specs)/|(^|/)(test_|.*[._-]test[._-])", p, re.I)), 25)}.',
             f'- Данные репозитория: {file_group(relevant, lambda p: Path(p).suffix.lower() in DATA_SUFFIXES, 25)}.',
             f'- Коммитов в пятичасовом окне: {len(commits)}; авторы: '
             +(', '.join(f'{safe_name(name)} {count}' for name,count in record['windowAuthors'].items()) or 'нет')+'.',
             f'- Все файлы и ветки: `{inventory}`.']
    for item in package_scripts:
        lines.append(f'- npm scripts в `{safe_name(item["path"])}`: '
                     +(', '.join(safe_name(name) for name in item['scriptNames']) or 'нет')+'.')
    for branch in branch_changes[:12]:
        paths = ', '.join(f'`{safe_name(path)}`' for path in branch['sample'][:12])
        lines.append(f'- Ветка `{safe_name(branch["branch"])}` до дедлайна: '
                     f'{branch["changedCount"]} отличающихся файлов; {paths or "без отличий"}.')
    if len(branch_changes) > 12:
        lines.append(f'- Ещё {len(branch_changes)-12} веток в полном инвентаре.')
    lines.append(f'- Структура предоставленных данных кейса (без содержимого): `{index_path}`.')
    for dataset in case_index['datasets'][:18]:
        fields = dataset.get('columns') or dataset.get('keys') or dataset.get('sheets') or []
        detail = ', '.join(safe_name(str(field)) for field in fields[:12])
        lines.append(f'  - `{safe_name(dataset["path"])}`: {dataset["format"]}, '
                     f'{dataset["bytes"]} байт'+(f'; поля/листы: {detail}' if detail else '')+'.')
    if len(case_index['datasets']) > 18:
        lines.append(f'  - Ещё {len(case_index["datasets"])-18} файлов в индексе.')
    markdown.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return markdown
