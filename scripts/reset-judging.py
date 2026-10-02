"""Archive the previous judging series and start an empty, recoverable series."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import judge_providers

ROOT = Path(__file__).resolve().parents[1]

def reset():
    proof = json.loads((ROOT/'data/judge-smoke/result.json').read_text(encoding='utf-8'))
    age = (datetime.now(timezone.utc)-datetime.fromisoformat(proof['at'])).total_seconds()
    if not proof['ok'] or age > 86400 or {j['id'] for j in proof['judges']} != {j['id'] for j in judge_providers.JUDGES}:
        raise RuntimeError('All three providers must pass fresh tool checks before reset')
    archive = ROOT/'data/judging-archive'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive.mkdir(parents=True,exist_ok=False)
    for relative in ('data/judging','data/judging-progress.json','data/eligibility-exclusions.json',
                     'web/data/reviews','docs/data/reviews'):
        source = (ROOT/relative).resolve()
        destination = (archive/relative).resolve()
        if not source.is_relative_to(ROOT) or not destination.is_relative_to(archive):
            raise RuntimeError('Archive path outside workspace')
        if source.exists():
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(source),str(destination))
    for relative in ('web/data/reviews','docs/data/reviews'):
        folder = ROOT/relative
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'index.json').write_text(json.dumps({'methodVersion':4,'reviews':[]}),encoding='utf-8')
    (ROOT/'data/judging').mkdir(parents=True,exist_ok=True)
    total = len(json.loads((ROOT/'web/data/catalog.json').read_text(encoding='utf-8'))['projects'])
    (ROOT/'data/judging-progress.json').write_text(json.dumps({'methodVersion':4,'total':total,'completed':0,
        'attempts':{},'archive':str(archive),'updatedAt':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    print(f'Archived previous reports: {archive}\nNew series: 0 / {total}')

if __name__ == '__main__':
    reset()
