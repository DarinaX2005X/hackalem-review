"""Publish the complete, already collected public README for each catalog project."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / 'web/data/catalog.json').read_text(encoding='utf-8'))
overrides = json.loads((ROOT / 'data/readme-overrides.json').read_text(encoding='utf-8'))
output = ROOT / 'web/data/readmes'
output.mkdir(parents=True, exist_ok=True)

missing = []
for project in catalog['projects']:
    name = project['id']
    cached = ROOT / 'data/readmes' / f'{name}.json'
    source = overrides.get(name)
    if source is None and cached.exists():
        source = json.loads(cached.read_text(encoding='utf-8'))
    if not source or not source.get('text'):
        missing.append(name)
        continue
    # Do not republish credentials embedded in a participant's public README.
    text = re.sub(r'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|AKIA[0-9A-Z]{16})\b',
                  '[REDACTED: API key]', source['text'])
    (output / f'{name}.md').write_text(text, encoding='utf-8')

print(f'Exported {len(catalog["projects"])-len(missing)} complete READMEs; missing: {len(missing)}')
if missing:
    print('Missing project ids:', ', '.join(missing[:20]))
