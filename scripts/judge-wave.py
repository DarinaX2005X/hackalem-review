"""Run a bounded wave of independent GPT-5.6 Luna reviews on D:.

Each project/judge pair gets a fresh session. Full events and reports remain
on C: while disposable clones and harness state on D: are cleaned.
"""

import argparse
import concurrent.futures
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('D:/hackalem-review-work')
CLONES = WORK / 'clones'
SCHEMA = ROOT / 'scripts/judge-report.schema.json'
TEMPLATE = (ROOT/'scripts/judge-prompt.txt').read_text(encoding='utf-8')
LIMIT_PATTERN = re.compile(r'\b(?:rate[ _-]?limit(?:ed|ing|[ _-]exceeded)?|usage[ _-]?limit(?:[ _-]reached)?|quota[ _-]?exceed(?:ed)?|too many requests|limit reached)\b|\b(?:HTTP(?:/\d(?:\.\d)?)?\s+|status(?:\s+code)?[\s:=]+)429\b',re.I)
START = datetime.fromisoformat('2026-09-23T08:00:00+00:00')
END = datetime.fromisoformat('2026-09-23T13:00:00+00:00')
CATALOG = json.loads((ROOT/'web/data/catalog.json').read_text(encoding='utf-8'))
PROJECTS = {p['id']:p for p in CATALOG['projects']}
BRIEFS = ROOT/'case-briefs'


def local_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DOSSIER = local_module('judge_dossier')
POLICY = local_module('review_policy')
PROVIDERS = local_module('judge_providers')
CHECKOUT = local_module('judge_checkout')
SNAPSHOT = local_module('judge_snapshot')
JUDGES = PROVIDERS.JUDGES
PUBLISHER = local_module('publish-reviews')


def api_requirements(repo_id, snapshot=None):
    path = ROOT/'data/api-requirements/projects'/f'{repo_id}.json'
    try:
        row = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return 'Инвентаризация не проведена. Наличие и доступность API не установлены.'
    variables = list({(item['name'], item['path'], item.get('snapshot')):
                      {key: item.get(key) for key in ('name', 'provider', 'kind', 'path', 'line', 'snapshot')}
                      for item in row.get('variables', []) if item.get('kind') != 'setting'
                      and (snapshot is None or item.get('snapshot') == snapshot)}.values())
    return json.dumps({'coverage': row.get('status'), 'variables': variables,
                       'inventoryFile': str(path), 'errors': row.get('errors', []),
                       'note': 'Variables above are for this snapshot; inspect inventoryFile if choosing another branch.',
                       'credentialsProvided': False}, ensure_ascii=False)

def git(*args, cwd=None, timeout=900, input=None):
    command=['git']
    if cwd is not None:
        command+=['-c',f'safe.directory={Path(cwd).resolve().as_posix()}']
    # Binary stdin preserves LF in Git's --stdin protocol on Windows.
    with subprocess.Popen([*command,*args],cwd=cwd,stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          env={**os.environ,'GIT_TERMINAL_PROMPT':'0'}) as p:
        try:
            stdout,stderr=p.communicate(input=input.encode('utf-8') if input is not None else None,
                                        timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
            else: p.kill()
            p.communicate()
            raise
    if p.returncode:
        raise RuntimeError(f"git {args[0]} failed: {stderr.decode('utf-8',errors='replace')[-600:]}")
    return stdout.decode('utf-8',errors='replace').strip()

def late_submission(clone, names, branches):
    """Find a first solution after the deadline, ignoring the generated README."""
    def template(snapshot):
        paths=git('ls-tree','-r','--name-only',snapshot,cwd=clone).splitlines()
        if paths!=['README.md']: return False
        readme=git('show',snapshot+':README.md',cwd=clone)
        return 'Hackathon team repository for ' in readme and len(readme)<250
    if any(not template(branch['commit']) for branch in branches): return None
    commits=[]
    for line in git('log','--format=%H%x1f%cI',*names,cwd=clone).splitlines():
        sha,instant=line.split('\x1f',1)
        when=datetime.fromisoformat(instant.replace('Z','+00:00')).astimezone(timezone.utc)
        if when>END:commits.append((when,sha,instant))
    for _,sha,instant in sorted(commits):
        if not template(sha):
            return {'reviewStatus':'late_submission','firstSolutionCommit':sha,
                    'firstSolutionCommitAt':instant,'deadlineUtc':END.isoformat(),
                    'reason':'First solution commit is after the deadline; code was not reviewed'}
    return None


def prepare(project, wave):
    repo_id = project['id']
    previous = WORK/'judge-wave-1'/repo_id
    clone = previous if (previous/'.git').exists() else CLONES/repo_id
    if not (clone/'.git').exists():
        clone.parent.mkdir(parents=True,exist_ok=True)
        # Fetch history metadata first; old multi-gigabyte datasets are not needed.
        git('clone','--quiet','--filter=blob:none','--no-checkout','--no-single-branch',
            project['url']+'.git',str(clone),timeout=1800)
    names = [line for line in git('branch','-r','--format=%(refname:short)',cwd=clone).splitlines()
             if line.startswith('origin/') and line!='origin/HEAD']
    if not names:
        # A timed-out clone may leave .git without any fetched branch refs.
        git('fetch','--filter=blob:none','origin','+refs/heads/*:refs/remotes/origin/*',cwd=clone,timeout=1800)
        names = [line for line in git('branch','-r','--format=%(refname:short)',cwd=clone).splitlines()
                 if line.startswith('origin/') and line!='origin/HEAD']
        if not names: raise RuntimeError('No fetched branch refs; repository preparation is incomplete')
    branches = []
    for name in names:
        sha = git('rev-list','-1','--before=2026-09-23T13:00:00Z',name,cwd=clone)
        if sha:
            branches.append({'name':name.removeprefix('origin/'),'commit':sha})
    snapshot_override=SNAPSHOT.override(ROOT,repo_id)
    branches=SNAPSHOT.apply(branches,snapshot_override,clone,git)
    if not branches:
        return {'repoId':repo_id,'eligible':False,'reason':'No pre-deadline branch commit',
                **(late_submission(clone,names,branches) or {})}
    default = next((b for b in branches if b['name']==project['defaultBranch']),None)
    if not default:
        default = max(branches,key=lambda b:git('show','-s','--format=%cI',b['commit'],cwd=clone))
    shas = list(dict.fromkeys(b['commit'] for b in branches))
    log = git('log','--format=%H%x1f%cI%x1f%aN',*shas,cwd=clone)
    commits = []
    for line in log.splitlines():
        fields = line.split('\x1f',2)
        if len(fields)!=3:
            continue
        sha,instant,author = fields
        when = datetime.fromisoformat(instant.replace('Z','+00:00')).astimezone(timezone.utc)
        if START <= when <= END:
            commits.append({'sha':sha,'time':instant,'author':author})
    if not commits:
        return {'repoId':repo_id,'eligible':False,'reason':'No commit in hackathon window',
                **(late_submission(clone,names,branches) or {})}
    CHECKOUT.hydrate_snapshot(clone, default['commit'], git)
    case_id = project['caseId']
    case_root = ROOT/'cases'/str(case_id)
    case_files = [str(p) for p in case_root.rglob('*') if p.is_file()]
    folder = wave/repo_id
    folder.mkdir(parents=True,exist_ok=True)
    manifest = {'repoId':repo_id,'caseId':case_id,'deadlineUtc':END.isoformat(),
                'defaultSnapshot':default['commit'],'branches':branches,
                'windowCommits':commits,'caseFiles':case_files}
    if snapshot_override:
        manifest['snapshotTimeEvidence']=snapshot_override
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    evidence_dir = ROOT/'data/judging'/repo_id
    evidence_dir.mkdir(parents=True,exist_ok=True)
    (evidence_dir/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    dossier = DOSSIER.build_dossier(project,clone,default['commit'],branches,commits,WORK,ROOT)
    (evidence_dir/'dossier.md').write_text(Path(dossier).read_text(encoding='utf-8'),encoding='utf-8')
    for label in (judge['label'] for judge in JUDGES):
        checkout = folder/label
        CHECKOUT.create_checkout(clone, checkout, default['commit'], git)
    return {'repoId':repo_id,'eligible':bool(commits),'folder':str(folder),
            'snapshot':default['commit'],'commits':len(commits),'dossier':str(dossier)}

def run_judge(job, model, wave):
    import jsonschema
    repo_id = job['repoId']
    project = PROJECTS[repo_id]
    judge = next(item for item in JUDGES if item['name'] == model)
    label = judge['label']
    report_dir = ROOT/'data/judging'/repo_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir/f'{label}.json'
    if report.exists():
        try:
            cached = json.loads(report.read_text(encoding='utf-8'))
            if (cached.get('methodVersion') == PROVIDERS.METHOD_VERSION
                    and cached.get('repoId') == repo_id and cached.get('caseId') == project['caseId']
                    and cached.get('snapshot') == job['snapshot'] and cached.get('model') == model):
                POLICY.validate_report_policy(cached, require_current=True, publication=True)
                return {'repoId':repo_id,'model':model,'status':'cached','score':cached.get('judgeScore')}
        except (ValueError,OSError,KeyError):
            pass
    folder = Path(job['folder'])
    # Streams and prompts survive deletion of temporary clones and containers.
    session = report_dir/f'session-{label}'
    session.mkdir(parents=True, exist_ok=True)
    checkout = folder/label
    working = folder/f'agent-{label}'
    working.mkdir(parents=True,exist_ok=True)
    attempt = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    raw = session/f'response-{attempt}.json'
    prompt = SNAPSHOT.prompt_note(SNAPSHOT.override(ROOT,repo_id))+'\n'+TEMPLATE.format(model=model,repo_url=project['url'],repo_id=repo_id,
                             checkout=checkout,snapshot=job['snapshot'],manifest=folder/'manifest.json',
                             global_criteria=ROOT/'criteries.md',case_id=project['caseId'],
                             task_file=ROOT/'cases'/str(project['caseId'])/'task.txt',
                             case_dir=ROOT/'cases'/str(project['caseId'])/'case-data',
                             case_brief=(BRIEFS/f"{project['caseId']:02}.md").read_text(encoding='utf-8'),
                             dossier=Path(job['dossier']).read_text(encoding='utf-8'),
                             capture_tool=ROOT/'scripts/judge-capture.py',capture_dir=session,
                             api_requirements=api_requirements(repo_id, job['snapshot']),
                             resource_prefix=f'{label}-{repo_id[5:13]}')
    prompt += f"\nПрочитай JSON Schema: {SCHEMA}. Запиши полный отчёт JSON в {raw}. Финальное сообщение может содержать путь. Не сокращай отчёт ради длины ответа.\n"
    prompt += f'\nПеред завершением выполни: python -X utf8 "{ROOT / "scripts/validate-judge-report.py"}" "{raw}". Если REPORT_INVALID, исправь свой отчёт по фактам и повтори проверку. Не выдумывай основания и не меняй баллы ради валидатора.\n'
    prompt += '\nНе останавливай процессы Windows/Linux по имени, PID или маске. Не выполняй общую очистку Docker, перезапуск Docker или WSL. Рабочие тесты запускай в своих именованных контейнерах; завершай только свои контейнеры через docker stop/docker rm. Общую очистку делает очередь.\n'
    path_map = folder/f'{label}-paths.json'
    if path_map.exists():
        prompt += ('\nОсобенность среды Windows: некоторые пути выгружены с экранированием. '
                   'Карта исходных и локальных путей: '+str(path_map)+'. '
                   'Для запуска распакуй полный исходный tar из карты внутри Linux-контейнера: '
                   'он сохраняет исходные имена и ссылки. Не считай ограничение Windows дефектом проекта.\n')
    prompt_file = session/f'prompt-{attempt}.txt'
    prompt_file.write_text(prompt, encoding='utf-8')
    events = session/f'events-{attempt}.jsonl'
    diagnostic_file = session/f'stderr-{attempt}.log'
    (session/f'attempt-{attempt}.json').write_text(json.dumps({
        'repoId':repo_id, 'modelId':judge['id'], 'wave':wave.name,
        'attempt':attempt, 'events':str(events)},ensure_ascii=False),encoding='utf-8')
    timed_out = False
    try:
        code = PROVIDERS.run_process(PROVIDERS.command(judge,prompt_file,working),working,
                                     events,diagnostic_file,PROVIDERS.environment(judge,working))
    except subprocess.TimeoutExpired as error:
        timed_out = True
        code = -1
        timeout_reason = getattr(error,'reason','time_budget')
    _, usage, errors, texts = PROVIDERS.event_summary(events)
    with (report_dir/f'{label}-usage.jsonl').open('a',encoding='utf-8') as ledger:
        ledger.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),
                                 'provider':judge['provider'],'modelId':judge['id'],
                                 'repoId':repo_id, 'wave':wave.name, 'attempt':attempt,
                                 'reasoning':os.environ.get('HACKALEM_JUDGE_REASONING','high'),
                                 'events':str(events), **usage})+'\n')
    diagnostic = diagnostic_file.read_text(encoding='utf-8',errors='replace')[-10000:]+'\n'+errors
    if code:
        status = 'rate_limited' if LIMIT_PATTERN.search(diagnostic) else 'timeout' if timed_out else f'exit-{code}'
        return {'repoId':repo_id,'model':model,'status':status,
                'reason':timeout_reason if timed_out else diagnostic[-1200:]}
    try:
        if not raw.exists():
            # Some harnesses return the JSON directly instead of writing a file.
            text = next((t for t in reversed(texts) if '"repoId"' in t), '')
            text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
            raw.write_text(text,encoding='utf-8')
        result = json.loads(raw.read_text(encoding='utf-8-sig'))
        jsonschema.validate(result,json.loads(SCHEMA.read_text(encoding='utf-8')))
        if result.get('repoId')!=repo_id or result.get('model')!=model or result.get('snapshot')!=job['snapshot']:
            raise ValueError('identity mismatch')
        POLICY.validate_report_policy(result, require_current=True)
        if result['assessmentStatus']=='ready': PUBLISHER.validate_judge(result,repo_id,model)
        temp = report.with_suffix('.json.tmp')
        temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temp,report)
        return {'repoId':repo_id,'model':model,'status':'complete' if result['assessmentStatus']=='ready' else 'incomplete',
                'score':result.get('judgeScore')}
    except (OSError,ValueError,jsonschema.ValidationError) as error:
        return {'repoId':repo_id,'model':model,'status':f'invalid: {str(error)[:500]}'}


def run_prepared(prepared, parallel, wave, emit=print, checkpoint=None, on_pair_complete=None, on_review_ready=None, on_status=None):
    """A slot is one agent, with fair project/model order and immediate publication."""
    from collections import deque
    pending = deque((row,judge['name']) for row in prepared if row['eligible'] for judge in JUDGES)
    results, completed_models = [], {}
    publication_failed=set()
    limited = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        active = {}
        def fill():
            while pending and len(active) < parallel and not limited:
                row,model = pending.popleft()
                active[pool.submit(run_judge,row,model,wave)] = (row,model)
        fill()
        while active:
            if on_status:
                on_status({'active':[{'repoId':row['repoId'],'model':model} for row,model in active.values()],
                           'waiting':len(pending),'finished':len(results),
                           'accepted':sum(r['status'] in ('complete','cached') for r in results),
                           'failures':sum(r['status'] not in ('complete','cached') for r in results)})
            finished,_ = concurrent.futures.wait(active,timeout=30,return_when=concurrent.futures.FIRST_COMPLETED)
            ready = []
            for future in finished:
                row,model = active.pop(future)
                try:
                    result = future.result()
                except Exception as error:
                    result = {'repoId':row['repoId'],'model':model,'status':f'error: {error}'}
                results.append(result)
                if checkpoint: checkpoint(results)
                if result['status'] not in ('complete', 'cached'):
                    emit(f"[{datetime.now().strftime('%H:%M:%S')}] ОШИБКА {row['repoId']} | {model}: {result['status']} (подробности в results.json)", flush=True)
                if result['status'] in ('complete','cached'):
                    if on_review_ready:
                        try:
                            if on_review_ready(row['repoId']) is False: publication_failed.add(row['repoId'])
                            else: publication_failed.discard(row['repoId'])
                        except Exception as error:
                            publication_failed.add(row['repoId'])
                            emit(f'Live publication failed: {error}',flush=True)
                    models_done = completed_models.setdefault(row['repoId'],set())
                    models_done.add(model)
                    if len(models_done) == len(JUDGES): ready.append(row['repoId'])
                if result['status'] == 'rate_limited': limited = True
            for repo_id in ready:
                if on_pair_complete:
                    try: on_pair_complete(repo_id)
                    except Exception as error: emit(f'Live publication failed for {repo_id}: {error}',flush=True)
                scores = ' / '.join(f"{r['model']}: {r.get('score', 'сохранено')}" for r in results
                                    if r['repoId'] == repo_id)
                emit(f"[{datetime.now().strftime('%H:%M:%S')}] {'СОХРАНЕНО, публикация не завершена' if repo_id in publication_failed else 'ГОТОВО'} {len([v for v in completed_models.values() if len(v) == len(JUDGES)])}/{len(prepared)} | {repo_id} | {scores}", flush=True)
            fill()
    for row,model in pending:
        results.append({'repoId':row['repoId'],'model':model,'status':'skipped_due_limit'})
    if checkpoint: checkpoint(results)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids',nargs='+',required=True)
    parser.add_argument('--parallel',type=int,default=8,help='maximum simultaneous GPT-5.6 Luna reviews')
    parser.add_argument('--wave-name',default='restart-1')
    parser.add_argument('--skip-priority',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    print(f'Codex: GPT-5.6 Luna; service tier={PROVIDERS.SERVICE_TIER}; '
          f'reasoning={os.environ.get("HACKALEM_JUDGE_REASONING", "high")}',flush=True)
    if args.parallel < 1:
        parser.error('parallel must be positive')
    try: PROVIDERS.require_subscription()
    except RuntimeError as error: parser.error(str(error))
    for judge in JUDGES:
        try: PROVIDERS.check_budget(judge)
        except RuntimeError as error: parser.error(str(error))
        if not PROVIDERS.executable(judge['provider']):
            parser.error(f"Missing CLI: {judge['provider']}")
    if not args.skip_priority:
        priority=local_module('judge_priority')
        if priority.run(ROOT,WORK,PROJECTS,args.ids,args.wave_name,local_module('judge-all')):
            # Propagate a genuine provider limit through the existing queue
            # protocol, so the already-running parent stops without retry charges.
            directory=WORK/'waves'/args.wave_name
            directory.mkdir(parents=True,exist_ok=True)
            (directory/'results.json').write_text(json.dumps([
                {'repoId':repo_id,'model':judge['name'],'status':'rate_limited'}
                for repo_id in args.ids for judge in JUDGES]),encoding='utf-8')
            raise SystemExit(1)
    wave = WORK/'waves'/args.wave_name
    wave.mkdir(parents=True,exist_ok=True)
    def safe_prepare(repo_id):
        try:
            result=prepare(PROJECTS[repo_id],wave)
            return result
        except Exception as error:
            return {'repoId':repo_id,'eligible':False,'error':str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8,len(args.ids))) as pool:
        prepared = list(pool.map(safe_prepare,args.ids))
    (wave/'prepared.json').write_text(json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in prepared:
        if row.get('error'):
            print('Preparation failed:',row['repoId'],row['error'],flush=True)
    def checkpoint(results):
        target=wave/'results.json'
        temporary=wave/'results.json.tmp'
        temporary.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,target)
    def publish_pair(repo_id):
        published=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/publish-reviews.py')],cwd=ROOT,
                                 capture_output=True,text=True,encoding='utf-8',errors='replace')
        if published.returncode:
            print('Live publication failed for',repo_id,(published.stdout+published.stderr)[-600:],flush=True)
            return False
        elif (ROOT/'web/data/reviews'/f'{repo_id}.json').exists():
            progress_file=ROOT/'data/judging-progress.json'
            try:
                progress=json.loads(progress_file.read_text(encoding='utf-8'))
                index=json.loads((ROOT/'web/data/reviews/index.json').read_text(encoding='utf-8'))
                progress['completed']=sum(row.get('status')=='complete' for row in index['reviews'])
                progress['updatedAt']=datetime.now(timezone.utc).isoformat()
                temporary=progress_file.with_suffix('.json.tmp')
                temporary.write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf-8')
                os.replace(temporary,progress_file)
            except (OSError,ValueError,KeyError) as error:
                print('Live progress update failed:',error,flush=True)
        server=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/ensure-local-server.py')],cwd=ROOT,
                              capture_output=True,text=True,encoding='utf-8',errors='replace')
        if server.returncode: print('Local site recovery failed:',server.stderr[-300:],flush=True)
        return (ROOT/'web/data/reviews'/f'{repo_id}.json').exists()
    def live_status(status):
        status.update({'wave':args.wave_name,'pid':os.getpid(),'updatedAt':datetime.now(timezone.utc).isoformat()})
        target=ROOT/'data/judging-live.json'
        temporary=target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,target)
    results = run_prepared(prepared,args.parallel,wave,checkpoint=checkpoint,on_review_ready=publish_pair,on_status=live_status)
    live_status({'active':[],'waiting':0,'finished':len(results),
                 'accepted':sum(r['status'] in ('complete','cached') for r in results),
                 'failures':sum(r['status'] not in ('complete','cached') for r in results), 'stopped':True})
    checkpoint(results)
    if any('error' in row for row in prepared) or any(row['status'] not in ('complete','cached') for row in results):
        sys.exit(1)

if __name__=='__main__':
    main()
