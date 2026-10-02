"""Recheck uncertain teams from all Git branches, without running repository code."""

import concurrent.futures
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = Path('D:/hackalem-review-work/team-audit')
START = datetime.fromisoformat('2026-09-23T08:00:00+00:00')
END = datetime.fromisoformat('2026-09-23T13:00:00+00:00')
catalog = json.loads((ROOT / 'web/data/catalog.json').read_text(encoding='utf-8'))
projects = [p for p in catalog['projects'] if p['teamSize'] is None or p['teamSize'] > 3]

def git(*args, cwd=None, timeout=300):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=timeout)

def audit(project):
    name = project['id']
    folder = DEST / name
    if not (folder / '.git').exists():
        result = git('clone', '--quiet', '--no-single-branch', project['url']+'.git', str(folder), timeout=600)
        if result.returncode:
            return {'id':name, 'error':result.stderr[-500:]}
    result = git('log', '--all', '--format=%H%x1f%aN%x1f%aE%x1f%cI%x1f%s', cwd=folder)
    if result.returncode:
        return {'id':name, 'error':result.stderr[-500:]}
    authors = {}
    in_window = set()
    for line in result.stdout.splitlines():
        fields = line.split('\x1f', 4)
        if len(fields) != 5:
            continue
        sha, display, email, instant, subject = fields
        when = datetime.fromisoformat(instant.replace('Z','+00:00')).astimezone(timezone.utc)
        if when > END:
            continue
        if re.search(r'bot|codex|claude|copilot|openai|github.actions|dependabot', display+' '+email, re.I):
            continue
        key = email.casefold().strip()
        row = authors.setdefault(key, {'email':email, 'names':set(), 'commits':0, 'window':0})
        row['names'].add(display)
        row['commits'] += 1
        if START <= when <= END:
            row['window'] += 1
            in_window.add(sha)
    output = {'id':name,'name':project['name'],'catalogMembers':project['members'],
              'branches':git('branch','-r','--format=%(refname:short)',cwd=folder).stdout.splitlines(),
              'humanAuthors':[{'email':v['email'],'names':sorted(v['names']),'commits':v['commits'],'window':v['window']} for v in authors.values()],
              'windowCommits':len(in_window)}
    return output

if __name__ == '__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for index, row in enumerate(pool.map(audit, projects),1):
            output.append(row)
            print(f'{index}/{len(projects)} {row["id"]}: {row.get("error", str(len(row["humanAuthors"]))+" author signatures")}', flush=True)
    path = ROOT / 'data/team-audit.json'
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved',path)
