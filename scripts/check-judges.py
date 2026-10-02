"""Exercise each fixed judge on a harmless fixture before a new judging series."""
import concurrent.futures
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import judge_providers as providers

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/judge-smoke'

def check(judge):
    folder = BASE/(judge['label']+'-'+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    nonce = uuid.uuid4().hex
    (folder/'fixture.txt').write_text(nonce, encoding='utf-8')
    expected = hashlib.sha256(nonce.encode()).hexdigest()
    (folder/'probe.py').write_text("from pathlib import Path\nimport hashlib\np=Path(__file__).parent\ns=hashlib.sha256((p/'fixture.txt').read_bytes()).hexdigest()\n(p/'executed.txt').write_text(s)\nprint(s)\n", encoding='utf-8')
    schema = {'type':'object','required':['fileContent','commandOutput','dockerOutput'],
              'properties':{name:{'type':'string'} for name in ('fileContent','commandOutput','dockerOutput')}}
    (folder/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    prompt = folder/'instructions.txt'
    prompt.write_text(
        f'This is a tool smoke test, not a participant review. Work only in {folder}. '
        'Do not use skills, browsers, UI tools, credentials, or read other directories. '
        f'Read {folder / "fixture.txt"} with a file tool. Execute python "{folder / "probe.py"}" with a shell tool. '
        f'Execute docker run --rm --network none --memory 128m --cpus 0.5 --name smoke-{judge["label"]} alpine:3.20 echo CONTAINER_READY. '
        f'Read {folder / "schema.json"}. Write observed fileContent, commandOutput and dockerOutput to {folder / "report.json"} as JSON. '
        'Never invent tool results. Do not modify fixture.txt or probe.py.', encoding='utf-8')
    events, diagnostic = folder/'events.jsonl', folder/'stderr.log'
    try:
        code = providers.run_process(providers.command(judge,prompt,folder),folder,events,diagnostic,
                                     providers.environment(judge,folder),timeout=300)
        session, usage, errors, texts = providers.event_summary(events)
        result = json.loads((folder/'report.json').read_text(encoding='utf-8-sig'))
        ok = (code == 0 and not errors and result['fileContent'].strip() == nonce
              and expected in result['commandOutput'] and 'CONTAINER_READY' in result['dockerOutput']
              and (folder/'executed.txt').read_text().strip() == expected)
        return {'model':judge['name'],'id':judge['id'],'ok':ok,'folder':str(folder),
                'usage':usage,'session':session,'errors':errors}
    except Exception as error:
        return {'model':judge['name'],'id':judge['id'],'ok':False,'folder':str(folder),'error':str(error)}

if __name__ == '__main__':
    providers.require_subscription()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(check, providers.JUDGES))
    result = {'methodVersion':providers.METHOD_VERSION,'at':datetime.now(timezone.utc).isoformat(),
              'ok':all(row['ok'] for row in rows),'judges':rows}
    BASE.mkdir(parents=True,exist_ok=True)
    (BASE/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['ok'] else 1)
